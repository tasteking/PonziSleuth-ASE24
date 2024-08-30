/**
 *Submitted for verification at Etherscan.io on 2017-01-20
*/

contract Vote {
    event LogVote(address indexed addr);

    function() {
        LogVote(msg.sender);

        if (msg.value > 0) {
            if (!msg.sender.send(msg.value)) {
                throw;
            }
        }
    }
}