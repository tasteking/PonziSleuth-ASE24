/**
 *Submitted for verification at Etherscan.io on 2016-11-09
*/

pragma solidity 0.4.4; // optimization enabled

contract SendBack {
    function() payable {
        if (!msg.sender.send(msg.value))
            throw;
    }
}