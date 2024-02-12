![img](./banner.png)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/sovrin-foundation/token-plugin/tree/ubuntu-20.04)


# Table of Contents

1.  [Sovrin Token Plugins](#org581a5d8)
    1.  [Announcements](#announcements)
    2.  [Install](#org6c5e3ee)
    3.  [Development Environment](#org003878b)
        1.  [Why cant I use my own local machine as my enviroment?](#orga843a17)
        2.  [How to Start Working with the Code](#orgf42e059)
        3.  [Alternative for running tests](#orga76b3c6)
    4.  [How To Contribute](#orgd389b14)

<a href="https://www.apache.org/licenses/LICENSE-2.0.txt" target="_blank">![Hex.pm](https://img.shields.io/hexpm/l/plug.svg?style=plastic)</a>
<a href="https://badge.fury.io/gh/sovrin-foundation%2Ftoken-plugin">[![GitHub version](https://badge.fury.io/gh/sovrin-foundation%2Flibsovtoken.svg)](https://badge.fury.io/gh/sovrin-foundation%2Ftoken-plugin)</a>

<a id="org581a5d8"></a>

# Sovrin Token Plugins

This repo contains the plugins to create the Sovrin payment ledger plugins: Token and Fees

<a id="org6c5e3ee"></a>

## Announcements

### February 12 2024

**_The project branches have changed._**

The `main` branch now contains the Ubuntu 20.04 work stream, and the previous `master` branch containing the Ubuntu 16.04 work stream has been moved to the `ubuntu-16.04` branch.

The following changes were made to the branches:
- `master` (default) renamed to `ubuntu-16.04`
  - This retargeted the associated PRs, which were then closed.
- `ubuntu-20.04` set as the default branch.
- `ubuntu-20.04` (default) renamed to `main`

**_Project sunset notice._**

The token plugins are being phased out.  There will be one final release of the Ubuntu 20.04 based code to be included in the `v1.2.0` release of the [Sovrin](https://github.com/sovrin-foundation/sovrin) package.  Subsequent releases of the [Sovrin](https://github.com/sovrin-foundation/sovrin) package will not contain the token plugins.

Following the Sovrin `v1.2.0` release this repository will be archived.

## Install

run the following command:

    ./build_indy_pool

<a id="org003878b"></a>

## Development Environment

<a id="orga843a17"></a>

### Why is a docker environment included?

We provide a docker environment that comes pre-loaded with all required dependencies and consider this to be the easiest way for any new developer to get setup and start testing their code.

<a id="orgf42e059"></a>

### How to Start Working with the Code

The preferred method of setting up the development environment is to use the devcontainers.
All configuration files for VSCode and [Gitpod](https://gitpod.io) are already placed in this repository.
If you are new to the concept of devcontainers in combination with VSCode [here](https://code.visualstudio.com/docs/remote/containers) is a good article about it.

Simply clone this repository and VSCode will most likely ask you to open it in the devcontainer, if you have the correct extension("ms-vscode-remote.remote-containers") installed.
If VSCode didn't ask to open it, open the command palette and use the `Remote-Containers: Rebuild and Reopen in Container` command.

If you want to use Gitpod simply use this [link](https://gitpod.io/#https://github.com/sovrin-foundation/token-plugin/tree/ubuntu-20.04)
or if you want to work with your fork, prefix the entire URL of your branch with  `gitpod.io/#` so that it looks like `https://gitpod.io/#https://github.com/sovrin-foundation/token-plugin/tree/ubuntu-20.04`.

Be aware that the automatic test discovery may need a kickstart via the command palette and `Python: Configure Tests`.

### Alternative for running tests

To use this script, you will need to use make as instructed above. Once you have the docker image running and synchronized, you can use run-test.sh to run individual tests.

We have a shell script to assist with running tests. Here's an example:

    ./run-test.sh token test_token_req_handler test_token_req_handler_MINT_PUBLIC_validate_missing_output

The first parameter is required. It can be either _token_ or _fees_. Anything else will return an error.

The remaining parameters are optional.

The second parameter is file name **without the .py**.

The third parameter is the name of the test.

1.  To run all sovtoken tests call it like this:

        ./run-test.sh token

2.  To run all sovtoken tests in a file, call it like this:

        ./run-test.sh token test_token_req_handler

<a id="orgd389b14"></a>

### Devops ci/cd

All ci/cd configuration for this project is stored within /devops . This includes a makefile used to build this project. Some useful make targets are:

1. image_ci builds the token-plugin image in the same manner as the ci/cd scripts. Defaults to building using a base 20.04 ubuntu image. can be customised by specifying the OSNAME ie **make image_ci OSNAME=xenial**
2. image_ci_xenial convenience target, results in the same build as **make image_ci OSNAME=xenial**
3. test_local_aws execute a local aws codebuild, first building the image, defaulting to a base ubuntu 20.04 image, configurable in the same method as above.

## How To Contribute

Please follow the guide [here](./docs/pull-request.md).
