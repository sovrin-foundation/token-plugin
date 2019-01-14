# Fixing on Batch Reject

## Problem 

Through testing we have seen view changes fail on the ledger casued by differing `state_root_hash` between the domain and payment ledger. This is caused by the payment ledger not being able to properly `revert`. The revert property is in charge of reverting `state_root_hash`.


## Tests

    1.test_num_uncommited_3pc_batches_with_fees_equal_to

        
    2.test_num_uncommited_3pc_batches_with_fees_not_equal_to

## Solution

After different [discussions](https://sovrin.atlassian.net/browse/ST-497) it's been decided that the best solution to this problem is to implement Indy-Plenum's [WriteRequestHandler](https://github.com/hyperledger/indy-plenum/blob/master/plenum/server/request_handlers/handler_interfaces/write_request_handler.py) and [BatchRequestHandler](https://github.com/hyperledger/indy-plenum/blob/master/plenum/server/batch_handlers/batch_request_handler.py) in FeesRequest handler. 

This will be similar to these handlers implementation of these two handlers in Indy-Node's [IdrCache](https://github.com/hyperledger/indy-node/blob/master/indy_node/persistence/idr_cache.py).