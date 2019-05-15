
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
