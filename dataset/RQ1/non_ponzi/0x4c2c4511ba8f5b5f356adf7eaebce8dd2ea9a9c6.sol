/**
 *Submitted for verification at Etherscan.io on 2016-11-19
*/

pragma solidity ^0.4.0;
contract BlockmaticsGraduationCertificate {
    address public owner = msg.sender;
    string certificate;


    function publishGraduatingClass(string cert) {
        if (msg.sender != owner)
            throw;
        certificate = cert;
    }


    function showBlockmaticsCertificate() constant returns (string) {
        return certificate;
    }
}