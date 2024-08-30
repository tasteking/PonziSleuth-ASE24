/**
 *Submitted for verification at Etherscan.io on 2016-11-06
*/

pragma solidity ^0.4.2;

contract storadge {
    
    event log(string description);
    
	function save(
        string mdhash
    )
    {
        log(mdhash);
    }
}