# Changelog

## 1.0.2
* TokenAuthNr needs to extend LedgerBasedAuthNr, not CoreAuthNr

## 1.0.1
* Hotfix: Request GET_UTXO needs to take into account max limit for a message
* GET_UTXO needs to use pagination to be able to return all unspent UTXOs regardless of max message size

## 1.0.0
* Apply new request handlers approach to Token Plugins
* Apply new request handlers approach to Token Req Handlers
* Apply new request handlers approach to Token FEEs Handlers
* Known Issue: Incorrect request validation
* Known Issue: Request GET_UTXO may fail if payment address contains too many UTXOs

## 0.9.13
* Added FeesAuthorizer
* Update SET_FEES and GET_FEES logic for Auth Rules
* Update GET_FEES to use aliases (GET_FEE request was added)
* Support TAA for XFER txn
* Register auth rule for MINT, XFER_PUBLIC and SET_FEES requests in auth_map
* Known Issue: Request GET_UTXO may fail if payment address contains too many UTXOs

## 0.9.3
* Changed FEES transaction to only allow a single change address.
* Changed CI/CD to new stable branch.
* CD added to the new stable branch with new stable release process
* Source code is now public Sovrin repository
* bugfixes

## 0.9.2
* Changed from using LevelDB to RocksDB
* Changed transactions to use JSON objects rather than unlabeled arrays
* Relies on indy-plenum and indy-crypto with BLS sigs fix
* bugfixes

## 0.9.1
* refactor to unify validation between fees and payments
* relies on stable versions of all artifacts
* Number of trustees required for MINT transaction set to 3
* UTXO cache optimization
* additional testing
* bugfixes

## 0.9.0

* Significant refactoring and updated tests
* Stability improvements
* Buqfixes

## 0.8.0

* A docker image that provides an easy-install build environment
* A CI/CD pipeline
    * that requires passing tests for merging
    * that requires signed commits
* Added sovtoken [transaction and response documentation](https://github.com/sovrin-foundation/token-plugin/tree/master/sovtoken/doc/Interface)
* Added sovtokenfees [transaction and response documentation](https://github.com/sovrin-foundation/token-plugin/tree/master/sovtokenfees/doc/Interface)
* Bugfixes


## 0.7.0
Initial release
