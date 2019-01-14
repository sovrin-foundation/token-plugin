# Fixing on Batch Reject

## Problem 

Through testing we have seen view changes fail on the ledger casued by differing `state_root_hash` between the domain and payment ledger. This is caused by the payment ledger not being able to properly `revert`. The revert property is in charge of reverting `state_root_hash`.

## Solution