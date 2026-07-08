CONTRACT_SOURCE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertChain {
    
    // Store certificate hashes
    mapping(string => uint256) private certificateTimestamps;
    mapping(string => address) private certificateIssuers;
    
    // Event emitted when certificate is stored
    event CertificateStored(
        string certificateHash,
        address issuer,
        uint256 timestamp
    );
    
    // Store a certificate hash on the blockchain
    function storeCertificate(string memory certificateHash) public {
        require(
            certificateTimestamps[certificateHash] == 0,
            "Certificate already exists on blockchain"
        );
        
        certificateTimestamps[certificateHash] = block.timestamp;
        certificateIssuers[certificateHash]    = msg.sender;
        
        emit CertificateStored(
            certificateHash,
            msg.sender,
            block.timestamp
        );
    }
    
    // Verify a certificate exists on blockchain
    function verifyCertificate(string memory certificateHash) 
        public view returns (bool exists, uint256 timestamp, address issuer) {
        
        uint256 ts = certificateTimestamps[certificateHash];
        
        if (ts == 0) {
            return (false, 0, address(0));
        }
        
        return (true, ts, certificateIssuers[certificateHash]);
    }
}
"""