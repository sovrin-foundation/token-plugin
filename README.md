# Plugins
source code and tests for Sovrin Ledger plugins

# Building the debian files for plugins
Run from the plugin repo root (you might need sudo)

``
SRC_DIR_NAME=sovtoken make -C devops package_in_docker
``

The above command has been only tested on Ubuntu

# Building the docker image
1. Copy the debian files for the plugins in `devops/build-scripts/xenial/Pool_Party`
2. Follow instructions at `devops/build-scripts/xenial/Pool_Party/README.org`