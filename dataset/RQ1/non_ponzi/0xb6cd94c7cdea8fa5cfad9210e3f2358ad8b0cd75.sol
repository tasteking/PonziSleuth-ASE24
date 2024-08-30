/**
 *Submitted for verification at Etherscan.io on 2017-02-07
*/

pragma solidity ^0.4.2;
contract BlockmaticsGraduationCertificate_02102017 {
    address public owner = msg.sender;
    string certificate;
    bool certIssued = false;

    function publishGraduatingClass(string cert) {
        if (msg.sender != owner || certIssued)
            throw;
        certIssued = true;
        certificate = cert;
    }

    function showBlockmaticsCertificate() constant returns (string) {
        return certificate;
    }
}