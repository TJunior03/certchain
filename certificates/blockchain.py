from web3 import Web3
from solcx import compile_source, install_solc
from .contract import CONTRACT_SOURCE
from .models import TransactionLog
import logging

logger = logging.getLogger(__name__)

# Ganache local blockchain URL
GANACHE_URL = "http://ganache:8545"


def get_web3():
    """Connect to local Ganache blockchain."""
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Ganache blockchain.")
    return w3


def deploy_contract():
    """
    Compile and deploy the CertChain smart contract to Ganache.
    Returns the deployed contract instance.
    """
    w3 = get_web3()

    # Install and use Solidity compiler
    install_solc("0.8.0")
    compiled = compile_source(
        CONTRACT_SOURCE,
        output_values=["abi", "bin"],
        solc_version="0.8.0"
    )

    # Get contract interface
    contract_id   = "<stdin>:CertChain"
    contract_interface = compiled[contract_id]

    # Use first Ganache account as deployer
    deployer = w3.eth.accounts[0]
    w3.eth.default_account = deployer

    # Deploy contract
    Contract = w3.eth.contract(
        abi=contract_interface["abi"],
        bytecode=contract_interface["bin"]
    )

    tx_hash    = Contract.constructor().transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    logger.info(f"Contract deployed at: {tx_receipt.contractAddress}")

    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=contract_interface["abi"]
    ), tx_receipt.contractAddress


def store_hash_on_blockchain(certificate_hash):
    """
    Store a certificate hash on the Ethereum blockchain.
    Returns the transaction hash as proof.
    """
    try:
        w3       = get_web3()
        contract, _ = deploy_contract()

        # Use first Ganache account
        account = w3.eth.accounts[0]
        w3.eth.default_account = account

        # Send transaction to blockchain
        tx_hash = contract.functions.storeCertificate(
            certificate_hash
        ).transact()

        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        tx_hash_hex = receipt.transactionHash.hex()

        logger.info(f"Hash stored on blockchain: {tx_hash_hex}")

        # Save to TransactionLog
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
    Returns exists, timestamp, issuer address.
    """
    try:
        w3 = get_web3()
        contract, _ = deploy_contract()

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