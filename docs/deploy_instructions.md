# Deployment Process

## Upgrade Ledger with Token Software

1) POOL_UPGRADE with the `indy-node` package version 1.6.70 to support `sovrin` package in POOL_UPGRADE txn
2) Upgrade the CLI (locally) to 1.6.6 libindy, indy-CLI
3) POOL_UPGRADE with the `sovrin` package version `1.1.20` to have TDE-ready version of plugins installed. **TODO:  This version is still a stub. Define first version with plugins and with trust anchor restriction**
It might be done with [POOL_UPGRADE](https://github.com/hyperledger/indy-node/blob/master/docs/pool-upgrade.md) transaction. You can do it from `indy-cli` with this command:
```
Command:
    ledger pool-upgrade - Send instructions to nodes to update themselves.

Usage:
    ledger pool-upgrade name=<name-value> version=<version-value> action=<action-value> sha256=<sha256-value> [timeout=<timeout-value>] [schedule=<schedule-value>] [justification=<justification-value>] [reinstall=<reinstall-value>] [force=<force-value>] [package=<package-value>]

Parameters are:
    name - Human-readable name for the upgrade.
    version - The version of indy-node package we perform upgrade to. 
                  Must be greater than existing one (or equal if reinstall flag is True)
    action - Upgrade type. Either start or cancel.
    sha256 - Sha256 hash of the package.
    timeout - (optional) Limits upgrade time on each Node.
    schedule - (optional) Node upgrade schedule. Schedule should contain identifiers of all nodes. Upgrade dates should be in future. 
                              If force flag is False, then it's required that time difference between each Upgrade must be not less than 5 minutes.
                              Requirements for schedule can be ignored by parameter force=true.
                              Schedule is mandatory for action=start.
    justification - (optional) Justification string for this particular Upgrade.
    reinstall - (optional) Whether it's allowed to re-install the same version. False by default.
    force - (optional) Whether we should apply transaction without waiting for consensus of this transaction. False by default.
    package - (optional) Package to be upgraded.

Examples:
    ledger pool-upgrade name=upgrade-1 version=2.0 action=start sha256=f284bdc3c1c9e24a494e285cb387c69510f28de51c15bb93179d9c7f28705398 schedule={"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv":"2020-01-25T12:49:05.258870+00:00"}
    ledger pool-upgrade name=upgrade-1 version=2.0 action=start sha256=f284bdc3c1c9e24a494e285cb387c69510f28de51c15bb93179d9c7f28705398 schedule={"Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv":"2020-01-25T12:49:05.258870+00:00"} package=some_package
    ledger pool-upgrade name=upgrade-1 version=2.0 action=cancel sha256=ac3eb2cc3ac9e24a494e285cb387c69510f28de51c15bb93179d9c7f28705398
```

## Mint Tokens

To mint tokens you need create a transaction, get an agreement (i.e. their signature) of 3 trustees (valid on 09/17/2018), and send it to the ledger. Steps:

1) Build MINT_PUBLIC transaction with this command:
    ```
    Command:
        ledger mint-prepare - Prepare MINT transaction.
    
    Usage:
            ledger mint-prepare outputs=<outputs-value> extra=<extra-value>
    
    Parameters are:
            outputs - The list of outputs in the following format: (recipient, amount)
            extra - Optional information for mint operation
    
    Examples:
            ledger mint-prepare outputs=(pay:sov:FYmoFw55GeQH7SRFa37dkx1d2dZ3zUF8ckg7wmL7ofN4,100)
            ledger mint-prepare outputs=(pay:sov:FYmoFw55GeQH7SRFa37dkx1d2dZ3zUF8ckg7wmL7ofN4,100),(pay:sov:ABABaaVwSascbaAShva7dkx1d2dZ3zUF8ckg7wmL7ofN4,5)
    ```
    You should get the output json of this command for the next step.
2) Get the signature of three trustees on the output json from the previous step.
    ```
    Command:
        ledger sign-multi - Add multi signature by current DID to transaction.
    
    Usage:
            ledger sign-multi txn=<txn-value>
    
    Parameters are:
            txn - Transaction to sign
    
    Examples:
            ledger sign-multi txn={"reqId":123456789,"type":"100"}
    ```
    When you collect the signature of one of the trustees next trustee should sign the json that was produced by previous one. As a result of this step you should have a json with at least three fields in an object in `signatures` field.
    
3) Send the signed transaction to the ledger. Use this command:
    ```
    Command:
            ledger custom - Send custom transaction to the Ledger.
    
    Usage:
            ledger custom <txn-value> [sign=<sign-value>]
    
    Parameters are:
            txn - Transaction json
            sign - (optional) Is signature required
    
    Examples:
            ledger custom {"reqId":1,"identifier":"V4SGRU86Z58d6TV7PBUe6f","operation":{"type":"105","dest":"V4SGRU86Z58d6TV7PBUe6f"},"protocolVersion":2}
            ledger custom {"reqId":2,"identifier":"V4SGRU86Z58d6TV7PBUe6f","operation":{"type":"1","dest":"VsKV7grR1BUE29mG2Fm2kX"},"protocolVersion":2} sign=true
    ``` 

## Distribute Tokens

Tokens can be distributed via `XFER_PUBLIC`. To make it we need to go through these steps (assume that we have payment address with tokens in our wallet and using `indy-cli`):

1) Get the UTXO for your payment address with this command: 
    ```
    Command:
            ledger get-payment-sources - Get sources list for payment address.
    
    Usage:
            ledger get-payment-sources payment_address=<payment_address-value>
    
    Parameters are:
            payment_address - Target payment address
    
    Examples:
            ledger get-payment-sources payment_address=pay:sov:GjZWsBLgZCR18aL468JAT7w9CZRiBnpxUPPgyQxh4voa
    ```

2) Send tokens to another address with this command:
    ```
    Command:
            ledger payment - Send request for doing payment.
    
    Usage:
            ledger payment inputs=<inputs-value> outputs=<outputs-value> extra=<extra-value>
    
    Parameters are:
            inputs - The list of payment sources
            outputs - The list of outputs in the following format: (recipient, amount)
            extra - Optional information for payment operation
    
    Examples:
            ledger payment inputs=txo:sov:rBuQo2A1sc9jrJg outputs=(pay:sov:FYmoFw55GeQH7SRFa37dkx1d2dZ3zUF8ckg7wmL7ofN4,100)
            ledger payment inputs=txo:sov:rBuQo2A1sc9jrJg,txo:sov:aEwACvA1sc9jrJg outputs=(pay:sov:FYmoFw55GeQH7SRFa37dkx1d2dZ3zUF8ckg7wmL7ofN4,100),(pay:sov:ABABefwrhscbaAShva7dkx1d2dZ3zUF8ckg7wmL7ofN4,5)
    ```
    You need to put the utxo from the first step to the inputs and all addresses that you need to transfer tokens to with the number of tokens to transfer. In addition, you have to add your payment address to the outputs with the number of change tokens, if there are any.

## Setting Fees Schedule

Setting fees process is similar to minting -- you need the build transaction, get the approval (signature) of trustees and to send it to the ledger. Details of this process are described in [setting fees guide](https://github.com/sovrin-foundation/libsovtoken/blob/master/doc/set_fees_process.md)

## Configure the ledger to remove the need for trust anchors

When fees are set for the transactions, we can allow to write to the ledger from DIDs that are not a trust anchor (of course if the have tokens to pay the fee). For this we need to make a POOL_UPGRADE once again for a `sovrin` package of version `1.1.21`. **TODO:  This version is still a stub yoo. Define first version with plugins and without trust anchor restriction**
 
    