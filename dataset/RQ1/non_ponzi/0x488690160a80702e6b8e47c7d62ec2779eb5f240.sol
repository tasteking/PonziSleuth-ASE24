/**
 *Submitted for verification at Etherscan.io on 2016-09-09
*/

contract SimpleStorage {
    uint storedData;
    address storedAddress;
    
    event flag(uint val, address addr);

    function set(uint x, address y) {
        storedData = x;
        storedAddress = y;
    }

    function get() constant returns (uint retVal, address retAddr) {
        return (storedData, storedAddress);
        flag(storedData, storedAddress);

    }
}