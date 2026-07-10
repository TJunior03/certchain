from web3 import Web3
from solcx import compile_source, install_solc
from .contract import CONTRACT_SOURCE
import logging

logger = logging.getLogger(__name__)

GANACHE_URL = "http://ganache:8545"

# Store contract address in memory for this session
_contract_address = None
_contract_abi = None


def get_web3():
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Ganache blockchain.")
    return w3


def get_contract():
    """
    Deploy contract once and reuse the same instance.
    """
    global _contract_address, _contract_abi

    w3 = get_web3()

    if _contract_address and _contract_abi:
        # Reuse existing contract
        return w3.eth.contract(
            address=_contract_address,
            abi=_contract_abi
        ), w3

    # First time — compile and deploy
    install_solc("0.8.0")
    compiled = compile_source(
        CONTRACT_SOURCE,
        output_values=["abi", "bin"],
        solc_version="0.8.0"
    )

    contract_id        = "<stdin>:CertChain"
    contract_interface = compiled[contract_id]
    _contract_abi      = contract_interface["abi"]

    deployer = w3.eth.accounts[0]
    w3.eth.default_account = deployer

    Contract = w3.eth.contract(
        abi=_contract_abi,
        bytecode=contract_interface["bin"]
    )

    tx_hash    = Contract.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    _contract_address = tx_receipt.contractAddress
    logger.info(f"Contract deployed at: {_contract_address}")

    return w3.eth.contract(
        address=_contract_address,
        abi=_contract_abi
    ), w3


def store_hash_on_blockchain(certificate_hash):
    """
    Store a certificate hash on the blockchain.
    """
    try:
        from .models import TransactionLog

        contract, w3 = get_contract()
        account = w3.eth.accounts[0]
        w3.eth.default_account = account

        tx_hash = contract.functions.storeCertificate(
            certificate_hash
        ).transact()

        receipt     = w3.eth.wait_for_transaction_receipt(tx_hash)
        tx_hash_hex = receipt.transactionHash.hex()

        logger.info(f"Hash stored on blockchain: {tx_hash_hex}")

        TransactionLog.objects.create(
            certificate_hash=certificate_hash,
            tx_hash=tx_hash_hex,
            blockchain="Ethereum (Ganache Local)"
        )

        return tx_hash_hex

    except Exception as e:
        logger.error(f"Blockchain error: {str(e)}")
        return None


def verify_hash_on_blockchain(certificate_hash):
    """
    Verify a certificate hash exists on the blockchain.
    """
    try:
        contract, w3 = get_contract()

        result = contract.functions.verifyCertificate(
            certificate_hash
        ).call()

        return {
            "exists"   : result[0],
            "timestamp": result[1],
            "issuer"   : result[2]
        }

    except Exception as e:
        logger.error(f"Blockchain verify error: {str(e)}")
        return {"exists": False, "timestamp": 0, "issuer": ""}