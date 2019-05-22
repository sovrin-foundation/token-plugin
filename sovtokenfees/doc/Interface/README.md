
# Sovtokenfees Data Structures
The format of sovtokenfees transactions requests and responses

## FEES transaction request
```
{
    <req_json>    //initial transaction request
    "fees":
    [
        [
            [<str: source payment address1>, <int: sequence number>],
        ],
        [
            [<str: change payment address1>, <int: amount of change>],
        ],
	    [<str: signature over source payment address1, sequence number, and all outputs>, ]
    ]
}
```
Example:
```
{
    <req_json>    //initial transaction request
    "fees":
    [
        [
	        ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
	    ],
	    [
	        ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
    	],
	    ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
}
```

## FEES transaction response
```
{
    "op": <str>,                //type of operation returned
    "protocolVersion":  <int>, // (optional) the version of the transaction response data structure
    "request":
    {
        "txn":
        {
            "data":
            {
                "alias": <str>,
                "dest": <str>,
                "verkey": <str>
            },
            "metadata":
            {
                "digest": <str>,
                "reqId": <str>
            },
            "protocolVersion": <int>,
            "type": "1"
        },
        "ver": <str>,
        "txnMetadata":
        {
            "seqNo": <int>,
            "txnTime": <int>
        },
        "reqSignature":
        {
            "type": <str>,
            "values":
            [
                {
                    "from": <str: DID that sent txn>,
                    "value": <str: signature of DID on txn>
                }
            ]
        },
        "rootHash": <str: root hash of ledger>,
        "auditPath":    // a list of strings
        [
            <str: hash of node in ledger>,
        ],
        "fees":
        {
            "inputs":   // a list of inputs
            [
                [<str: payment address>, <int: sequence number>],
            ],
            "outputs":
            [
                [<str: payment address>, <int: amount>]
            ],
            "fees": <int: amount>,
            "ref": <str: reference to txn for which fees were paid>,
            "reqSignature":
            {
                "type": <str: signature type>,
                "values":   // a list of signatures
                [
                    {
                        "from": <str: first input payment address>,
                        "value": <str: signature of payment address on outputs>
                    },
                ]
            },
            "txnMetadata":
            {
                "seqNo": <int: sequence number>,
                "txnTime": <int: seconds since the unix epoch>
            },
            "rootHash": <str: root hash of ledger>,
            "auditPath":    // a list of strings
            [
                <str: hash of node in ledger>,
            ]
        }
    }
}
```
Example:
```
{
    "op": "REPLY",
    "protocolVersion": 1,
    "request":
    {
        "txn":
        {
            "data":
            {
                "alias": "508867",
                "dest": "8Wv7NMbsMiNSmNa3iC6fG7",
                "verkey": "56b9wim9b3dYXzzc8wnm8RZePbyuMoWw5XUXxL4Y9gFZ"
            },
            "metadata":
            {
                "digest": "54289ff3f7853891e2ba9f4edb4925a0028840008395ea717df8b1f757c4fc77",
                "reqId": 1529697827844532830
            },
            "protocolVersion": 2,
            "type": "1"
        },
        "ver": 1,
        "txnMetadata":
        {
            "seqNo": 13,
            "txnTime": 1529697829
        },
        "reqSignature":
        {
            "type": "ED25519",
            "values":
            [
                {
                    "from": "MSjKTWkPLtYoPEaTF1TUDb",
                    "value": "5Ngg5fQ4NtqdzgN3kSjdRKo6ffeq5sP264TmzxvGGQX3ieJzP9hCeUCu7RkmAhLjzqZ2Z5y8FLSptWxetS8FCmcs"
                }
            ]
        },
        "rootHash": "FePFuqEX6iJ1SP5DkYn9WTXQrThxqevEkxYXyCxyX4Fd",
        "auditPath":
        [
            "CWQ9keGzhBqyMRLvp7XbMr7da7yUbEU4qGTfJ2KNxMM6",
            "2S9HAxKukY2hxUoEC718fhywF3KRfwPnEQvRsoN168EV"
        ],
        "fees":
        {
            "inputs":
            [
                ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
            ],
            "outputs":
            [
                ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
            ],
            "fees": 4,
            "ref": "1:13",
            "reqSignature":
            {
                "type": "ED25519",
                "values":
                [
                    {
                        "from": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es",
                        "value": "5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"
                    }
                ]
            },
            "txnMetadata":
            {
                "seqNo": 2,
                "txnTime": 1529697829
            },
            "rootHash": "A8qwQKyKUMd3PnJTKe4bXRzajCUVgSd1J1A7jdahhNW6",
            "auditPath": ["Gyw5iBPPs4KSiEoAXQcjv8jw1VWsFjTVyCkm1Zp9E3Pa"]
        }
    }
}
```
## SET_FEES transaction request
```
{
    "reqId": <int>,             //random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "operation": {
        "type": "20000",
        "fees": {
            <str: feesAlias>: <int: amount>,
        }
    },
}
```

Example:
```
{
    "reqId": 1527801087197612,
    "protocolVersion": 1,
    "operation": {
        "type": "20000",
        "fees": {
            "1": 4,
            "10001": 8
        }
    }
}
```

## GET_FEES transaction request
```
{
    "identifier": <str>,        // the submitter DID
    "reqId": <int>,             // a random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "operation": {
        "type": "20001"
    }
}
```
Example:
```
{
    "identifier": "6ouriXMZkLeHsuXrN1X1fd",
    "reqId": 47660,
    "protocolVersion": 1,
    "operation": {
        "type": "20001"
    }
}
```

## GET_FEES response
```
{
    "op": "REPLY",
    "result": {
        "identifier": <str>,        // the submitter DID
        "reqId": <int>,             // a random identifier
        "type": "20001",
        "fees": {
            <str: feesAlias>: <int: amount>,
        },
        "state_proof": {
            {
                "participants": [ <str>, ], // the nodes that participated in consensus
                "signature": <str> // the BLS signature of the nodes
                "value":
                {
                    "ledger_id": <int>, // the associated ledger where the state proof came from
                    "pool_state_root_hash": <str>, // the state proof root hash of the pool ledger
                    "state_root_hash": <str>, // the state proof root hash of the total ledgers
                    "timestamp": <int>, // the time the transaction was committed
                    "txn_root_hash": <str> // the transaction root hash of the transaction on a specific ledger
                }
            },
            "rootHash": <str>,      // the root hash of the transaction
            "proof_nodes": <str>,   // the hash of each node in the path
        }
    }
}
```

Example:
```
{
    "op": "REPLY",
    "result":
    {
        "identifier": "6ouriXMZkLeHsuXrN1X1fd",
        "reqId": 10378,
        "type": "20001",
        "fees":
        {
            "1": 4,
            "10001": 8
        },
        "state_proof":
        {
            "multi_signature": {//TODO add valid json string in here},
            "proof_nodes": "29qFIGZlZXOT0pF7IjEiOjQsIjEwMDAxIjo4fQ==",
            "root_hash": "5BU5Rc3sRtTJB6tVprGiTSqiRaa9o6ei11MjH4Vu16ms"
        },
    }
}
```

## GET_FEE transaction request
```
{
    "identifier": <str>,        // the submitter DID
    "reqId": <int>,             // a random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "operation": {
        "type": "20001",
        "alias": <str: feesAlias>
    }
}
```
Example:
```
{
    "identifier": "6ouriXMZkLeHsuXrN1X1fd",
    "reqId": 47660,
    "protocolVersion": 1,
    "operation": {
        "type": "20001",
        "alias": "nym_fees"
    }
}
```

## GET_FEE response
```
{
    "op": "REPLY",
    "result": {
        "identifier": <str>,        // the submitter DID
        "reqId": <int>,             // a random identifier
        "type": "20001",
        "fee": <int: amount>,
        "state_proof": {
            {
                "participants": [ <str>, ], // the nodes that participated in consensus
                "signature": <str> // the BLS signature of the nodes
                "value":
                {
                    "ledger_id": <int>, // the associated ledger where the state proof came from
                    "pool_state_root_hash": <str>, // the state proof root hash of the pool ledger
                    "state_root_hash": <str>, // the state proof root hash of the total ledgers
                    "timestamp": <int>, // the time the transaction was committed
                    "txn_root_hash": <str> // the transaction root hash of the transaction on a specific ledger
                }
            },
            "rootHash": <str>,      // the root hash of the transaction
            "proof_nodes": <str>,   // the hash of each node in the path
        }
    }
}
```

Example:
```
{
    "op": "REPLY",
    "result":
    {
        "identifier": "6ouriXMZkLeHsuXrN1X1fd",
        "reqId": 10378,
        "type": "20001",
        "fee": 10,
        "state_proof":
        {
            "multi_signature": {//TODO add valid json string in here},
            "proof_nodes": "29qFIGZlZXOT0pF7IjEiOjQsIjEwMDAxIjo4fQ==",
            "root_hash": "5BU5Rc3sRtTJB6tVprGiTSqiRaa9o6ei11MjH4Vu16ms"
        },
    }
}
```

## How to set fees for an action
 For setting fees for an action we need to make the following steps:
 * Send a SET_FEES txn with appropriate amount for required alias. 
 For example, we have an alias, like "add_new_steward" (and we want to set fees for adding new nym action). For setting fees for this alias, we need to send a SET_FEES transaction with map {"add_new_steward": 42}.
 Txn will be looked as:
 ```
{
    "reqId": <int>,             //random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "operation": {
        "type": "20000",
        "fees": {
            "add_new_steward": 42,,
        }
    },
}
```
 * After that, we need to add metadata into default auth constraint for action "add new nym".
 For this example, txn for changing metadata for default auth_rule will be looked as:
 ```
{
    'operation': {
           'type':'120',
           'constraint':{
                    'constraint_id': 'ROLE', 
                    'role': '0',
                    'sig_count': 1, 
                    'need_to_be_owner': False, 
                    'metadata': {'fees': 'add_new_steward'}
           }, 
           'field' :'role',
           'auth_type': '1', 
           'auth_action': 'ADD',
           'new_value': '2'
    },
    
    'identifier': <str: some identifier>,
    'reqId': <int: timestamp>,
    'protocolVersion': 1,
    'signature': <str: signature>
}
```

The pool performs the following validation for the given example:
* doDynamicValidation for "adding new steward" nym (_`from indy-node's side`_);
    * making general role's authorization (_`from indy-node's side`_)
    * making fees specific validation, using metadata field (_`from plugin's side`_)
        * lookup through config state for getting amount of "add_new_steward" alias (_`from plugin's side`_)
        * making can_pay_fees validation (_`from plugin's side`_)
        
### Notes:
* The order of previous steps is very important. First of all SET_FEES is required, then - AUTH_RULE.
* SET_FEES is "updating" transaction, so that it appends new aliases to the existing FEEs map (either adding or overriding aliases). For example, if current fees are {A: 1, B: 2} then after sending SET_FEES transaction with {A: 42, C:3}, the resulted map will look like {A: 42, B: 2, C:3}. 
* Setting fees without adding or changing metadata in corresponding auth_rule doesn't have any effect.
        
## How to setup fees for whole pool
For setting fees for whole we need to make the following steps:
* Define all the actions which we would like to set fees for
* Repeat all the steps from [How to set fees for an action](#how-to-set-fees-for-an-action) for each action

## How to change fees amount for alias
For changing amount of fees for existing alias, you need to send a SET_FEES (as described in [How to set fees for an action](#how-to-set-fees-for-an-action)) transaction with 'fees' value, like:
```
{<str: fees alias to change>: <int: new amount>}
```
As was mentioned before, SET_FEES is "updating" transaction and this request will update whole fees map in state and new amount of fees_alias will be used for validation.
Full SET_FEES request:
 ```
{
    "reqId": <int>,             //random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "operation": {
        "type": "20000",
        "fees": {
            <str: fees alias to change>: <int: new amount>,
        }
    },
}
```

## How to set fees for complex Auth Constraints
For example, we have a constraint like:
```
(TRUSTEE, 2) or (STEWARD, 5)
```
It means, that this action requires "2 signatures from 2 different TRUSTEEs" or "5 signatures from 5 different STEWARDs" and we want to set fees for steward's part of this constraint.
For this case, we need to:
* add new alias, 'some_action_by_steward' for example, as described in [How to set fees for an action](#how-to-set-fees-for-an-action)
* set this alias for corresponding auth_rule into steward's part of constraint:
```
(TRUSTEE, 2) or (STEWARD, 5, 'fees': 'some_action_by_steward')
```
After that, the next requests will be ordered:
* with 2 and more TRUSTEE's signatures
* with 5 and more STEWARD's signature and required amount of fees.

Also, trustee's part of constraint can contains 'fees' field with different fees alias, like:
```
(TRUSTEE, 2, 'fees': 'some_action_by_trustee') or (STEWARD, 5, 'fees': 'some_action_by_steward')
``` 
'some_action_by_trustee' should exists before setting it in AUTH_RULE transaction.

## Recommendation for setting fees.
* **If you want to set an alias for `AND` constraint, then make sure, that all of fees aliases will have the same amount.**
In the other words, fees aliases can be different, but amount should be the same.
For example, there is a constraint:
```
(TRUSTEE, 2) and (STEWARD, 3)    - it means, that 1 trustee's and 3 steward's signatures are required
```
And we want to setup fees, like:
```
(TRUSTEE, 2, {'fees': 'trustees_fees'}) and (STEWARD, 3, {'fees': 'steward_fees'})
```
And after all setup actions we try to send a request with fees, related to 'trustees_fees' alias and signatures from 1 TRUSTEE and 3 STEWARD.
In this case, if amount of 'trustees_fees' doesn't equal to amount of 'steward_fees' then RequestRejectedException will be raised.
* **Either do not set FEEs for NODE txn, or set equal amount of Fees for all fields (except service)**
For now, we can add only 1 fees field per request, but Node txn can contain several actions so that validation process (including fees validation) will be called for each action. 
For example we can change ip address, port and alias in 1 txn, but 1 fees field would be used for each action validation.
If each of this actions cost 5 tokens, then Node request with 15 token will be rejected, because we don't summarize all action's tokens during validation process.
But Node request with 5 tokens will be ordered.