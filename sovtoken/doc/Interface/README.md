
# Sovtoken Data Structures
The format of sovtoken transactions requests and responses

## GET_UTXO transaction request
```
{
    "identifier": <str>,        // submitter of txn; normally a DID, but for payments, a payment addr
    "operation":
    {
        "address": <str>,       // the payment address for which we're seeking UTXOs
        "type": 10002           // the numeric txn id of "GET_UTXO"
    },
    "reqId": <int>,             // a random identifier
    "protocolVersion": <int>    // (optional)  the version of the client/node communication protocol
}

```
Example:
```

{
    "identifier": "2jyMWLv8NuxUV4yDc46mLQMn9WUUzeKURX3d2yQqgoLqEQC2sf",
    "operation":
    {
        "address": "2jyMWLv8NuxUV4yDc46mLQMn9WUUzeKURX3d2yQqgoLqEQC2sf",
        "type": "10002"
    },
    "reqId": 6284,
    "protocolVersion": 1
}

```

## GET_UTXO response
```
{
    "op": "REPLY",
    "protocolVersion": <int>    // (optional)  the version of the client/node communication protocol
    "result": {
        "type": "10002",
        "address": <str>,       // the payment address
        "identifier": <str>,    // the payment address
        "reqId": <int>,         // a random identifier
        "outputs": [
            ["<str: address>", <int: sequence number>, <int: amount>],
        ],
        "state_proof":
        {
            "multi_signature":
            {
                "participants": [ <str>, ],
                "signature": <str>
                "value":
                {
                    "ledger_id": <int>,
                    "pool_state_root_hash": <str>,
                    "state_root_hash": <str>,
                    "timestamp": <int>,
                    "txn_root_hash": <str>
                }
            },
            "proof_nodes": <str>,
            "root_hash": <str>
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
        "type": "10002",
        "address": "dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q",
        "identifier": "6ouriXMZkLeHsuXrN1X1fd",
        "reqId": 15424,
        "outputs":
        [
            ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 1, 40]
        ],
        "state_proof":
        {
            "multi_signature":
            {
                "participants": ["Gamma", "Alpha", "Delta"],
                "signature": "RNUfcr74ekwBxsT7mxnT2RDFaRRYbfuhebnqQW9PsGkf1bsKC8m8DAqsFfMMLGgAy9CSWM8cyXRUdWLrKUywTajbySfy18oxxdg8ZZApGYHZtiuj6y9sbScAyMwWMmxrDErrj8DWVEVZbGMhPnSSUkmkC6SBnZtSDfdRDvHUMQVBRR",
                "value":
                {
                    "ledger_id": 1001,
                    "pool_state_root_hash": "9i3acxaDhCfx9jWXW2JZRoDWzRQEKo7bPBVN7VPE1Jhg",
                    "state_root_hash": "8tJkWdp9wdz3bpb5s5hPDfrjWCQTPmsFKrSdoPmTTnea",
                    "timestamp": 1529705683,
                    "txn_root_hash": "67khbUNo8rySwEtW2SPSsyK4rmLCS7JAN4kYnppELajc"
                }
            },
            "proof_nodes": "+I74ObM0Y3RLU1hCYnYyTXkzVEdHVWdURmpreHUxQTlKTTNTc2NkNUZ5ZFk0ZGt4bmZ3QTdxOjGEw4I0MPhRgICAgICAoKwYfN+WIsLFSOuMjp224HzlSFoSXhXc1+rE\\/vB8jh7MoF\\/sqT9NVI\\/hFuFzQ8LUFSymIKOpOG9nepF29+TB2bWOgICAgICAgICA",
            "root_hash": "8tJkWdp9wdz3bpb5s5hPDfrjWCQTPmsFKrSdoPmTTnea"
        }
    }
}

```

## XFER_PUBLIC transaction request
    note: any difference between the sum of the inputs and the sum of outputs
    used to be the fees amount, but now renders the txn invalid
```
{
    "identifier": <str>,        // first <source payment address w/o checksum>
    "reqId": <int>,             // a random identifier
    "protocolVersion": <int>,   // (optional) the protocol version
    "operation": {
        "type": "10001",
        "inputs": [
            [<str: source payment address>, <int: sequence number>],
        ],
        "outputs": [
            [<str: change payment address>, <int: amount of change>],
        ],
        "extra": <str>,     // optional field
        "signatures": [
            <string: signature over source payment address, sequence number, and all outputs>,
        ]
    }
}
```
Example:
```
{
    "identifier": "6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1",
    "reqId": 1529682415342024,
    "protocolVersion": 2,
    "operation":
    {
        "type": "10001",
        "inputs":
        [
            ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 1]
        ],
        "outputs":
        [
            ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 13],
            ["24xHHVDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY", 13],
            ["mNYFWv9vvoQVCVLrSpbU7ZScthjNJMQxMs3gREQrwcJC1DsG5", 13],
            ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 1]
        ],
        "extra": None,
        "signatures": ["4fFVD1HSVLaVdMpjHU168eviqWDxKrWYx1fRxw4DDLjg4XZXwya7UdcvVty81pYFcng244tS36WbshCeznC8ZN5Z"]
    }
}
```

## XFER_PUBLIC response
```
{
    "op": <str>,        //type of operation returned
    "protocolVersion": <int>,   // (optional) the protocol version
    "result":
    {
        "txn":
        {
            "data":
            {
                "inputs": [
                    [<str: source payment address>, <int: sequence number>],
                ],
                "outputs": [
                    [<str: change payment address>, <int: amount>],
                ],
                "extra": <str>,     // optional field
            },
            "metadata":
            {
                "digest": <str>,    //
                "from": <str>,      // one of the input payment addresses
                "reqId": <int>      // a random identifier
            },
            "protocolVersion": <int>,
            "type": "10001"
        },
        "ver": <str>,
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
```

Example:
```
{
    "op": "REPLY",
    "protocolVersion": 2,
    "result":
    {
        "txn":
        {
            "data":
            {
                "extra": None,
                "inputs":
                [
                    ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 1]
                ],
                "outputs":
                [
                    ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 13],
                    ["24xHHVDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY", 13],
                    ["mNYFWv9vvoQVCVLrSpbU7ZScthjNJMQxMs3gREQrwcJC1DsG5", 13],
                    ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 1]
                ]
            },
            "metadata":
            {
                "digest": "228af6a0c773cbbd575bf4e16f9144c2eaa615fa81fdcc3d06b83e20a92e5989",
                "from": "6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1",
                "reqId": 1529682415342024
            },
            "protocolVersion": 2,
            "type": "10001"
        },
        "reqSignature":
        {
            "type": "ED25519",
            "values":
            [
                {
                    "from": "dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q",
                    "value": "4fFVD1HSVLaVdMpjHU168eviqWDxKrWYx1fRxw4DDLjg4XZXwya7UdcvVty81pYFcng244tS36WbshCeznC8ZN5Z"
                }
            ]
        },
        "txnMetadata":
        {
            "seqNo": 2,
            "txnTime": 1529682415
        },
        "ver": "1",
        "auditPath": ["5NtSQUXaZvETP1KEWi8LaxSb9gGa2Qj31xKQoimNxCAT"],
        "rootHash": "GJFwiQt9r7n25PqM1oXBtRceXCeoqoCBcJmRH1c8fVTs"
    }
}
```
## MINT transaction request
```
{
    "reqId": <int>,             // a random identifier
    "protocolVersion": <int>,   // the version of the client/node communication protocol
    "identifier": <string>
    "operation": {
        "type": "10000",
        "outputs": [
            [<str: output payment address>, <int: amount to mint>],
        ]
    }
}
```
Example:
```
{
    "reqId": 1527799618700635,
    "protocolVersion": 2,
    "identifier": "V4SGRU86Z58d6TV7PBUe6f"
    "operation": {
        "type": "10000",
        "outputs": [
            ["sjw1ceG7wtym3VcnyaYtf1xo37gCUQHDR5VWcKWNPLRZ1X8eC", 60],
            ["dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", 40]
        ]
    }
}
```
