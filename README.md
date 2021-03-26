![img](./banner.png)

# Table of Contents

1.  [Sovrin Token Plugins](#org581a5d8)
    1.  [Install](#org6c5e3ee)
    2.  [Development Environment](#org003878b)
        1.  [Why cant I use my own local machine as my enviroment?](#orga843a17)
        2.  [Requirements](#orgf42e059)
        3.  [Installing docker-sync](#orge005da4)
        4.  [Starting Dev Env](#orgb33d5f6)
        5.  [Alternative for running tests](#orga76b3c6)
    3.  [How To Contribute](#orgd389b14)

<a href="https://www.apache.org/licenses/LICENSE-2.0.txt" target="_blank">![Hex.pm](https://img.shields.io/hexpm/l/plug.svg?style=plastic)</a>
<a href="https://badge.fury.io/gh/sovrin-foundation%2Ftoken-plugin">[![GitHub version](https://badge.fury.io/gh/sovrin-foundation%2Flibsovtoken.svg)](https://badge.fury.io/gh/sovrin-foundation%2Ftoken-plugin)</a>

<a id="org581a5d8"></a>

# Sovrin Token Plugins

This repo contains the plugins to create the Sovrin payment ledger plugins: Token and Fees

<a id="org6c5e3ee"></a>

## Install

run the following command:

    ./build_indy_pool

<a id="org003878b"></a>

## Development Environment

<a id="orga843a17"></a>

### Why is a docker environment included?

We provide a docker environment that comes pre-loaded with all required dependencies and consider this to be the easiest way for any new developer to get setup and start testing their code.

<a id="orgf42e059"></a>

### Requirements

- [docker](https://www.docker.com/get-docker)
- [docker-compose](https://docs.docker.com/compose/)
- [docker-sync](https://github.com/EugenMayer/docker-sync)
- ruby
- gem

### Running on Windows

This repo utilizes docker-sync which will not run natively on Windows. The following steps can be used to run the Dev Environment on Windows via WSL.

1. Install the relevant WSL Ubuntu distro on your machine via the Windows store (currently 18.04). Note, ensure that the Windows Subsystem for Linux is enabled under **Turn Windows features on or off**
2. Within Docker -> Settings -> General, ensure that **Use the WSL 2 based engine is checked** and **Expose Docker daemon on tcp://localhost:2375 without TLS** is unchecked.
3. Within Docker -> Settings -> Resources -> WSL Integration ensure that your installed WSL Ubuntu distro is checked. refer to this [docker doc](https://docs.docker.com/docker-for-windows/wsl/) for more help if required
4. Open your WSL terminal and install the following dependencies:
5. Complete steps 3-10, **skipping step 8 and step 4** of the [docker sync setup](https://docker-sync.readthedocs.io/en/latest/getting-started/installation.html#let-s-go) Step 8 is not required as WSL 2 does not require insecure Docker settings.
6. Navigate to /mnt/YOUR_REPO_DIRECTORY within wsl. You can now run all of the below commands.

<a id="orge005da4"></a>

### Installing docker-sync

    gem install docker-sync

<a id="orgb33d5f6"></a>

### Starting Dev Env

**PLEASE OPEN TWO TERMINAL WINDOWS**

In the first window:

    make start

This will run docker-sync-stack start. It will compose the docker container
and mount your local directory.

In the second window:

    make setup

This will fix config files and install sovtoken and sovtoken fees

Now we run our test:

    make test

when you're all done using sync just use:

    make clean

<a id="orga76b3c6"></a>

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

## How To Contribute

Please follow the guide [here](./docs/pull-request.md).
