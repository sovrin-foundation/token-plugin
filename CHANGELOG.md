# Changelog

## 0.9.3
* Changed FEES transaction to only allow a single change address.
* Changed CI/CD to new stable branch.
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
* Added sovtoken [transaction and response documentation](https://github.com/evernym/plugin/tree/master/sovtoken/doc/Interface)
* Added sovtokenfees [transaction and response documentation](https://github.com/evernym/plugin/tree/master/sovtokenfees/doc/Interface)
* Bugfixes


## 0.7.0
Initial release