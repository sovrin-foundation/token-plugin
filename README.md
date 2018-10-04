
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

![img](./banner.png)


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

### Why cant I use my own local machine as my enviroment?

Due to some compatibility issues we have decided that a docker enviroment would be the easiest way
for any new developer to get setup and start testing their code.


<a id="orgf42e059"></a>

### Requirements

-   [docker](https://www.docker.com/get-docker)
-   [docker-compose](https://docs.docker.com/compose/)
-   [docker-sync](https://github.com/EugenMayer/docker-sync)
-   ruby
-   gem


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

    make deps
    make setup

This will fix config files and install sovtoken and sovtoken fees

Now we run our test:

    make test

when you're all done using sync just use:

    make clean 


<a id="orga76b3c6"></a>

### Alternative for running tests

To use this script, you will need to use make as instructed above.  Once you have the docker image running and synchronized, you can use run-test.sh to run individual tests.

We have a shell script to assist with running tests.  Here's an example:

    ./run-test.sh token test_token_req_handler test_token_req_handler_MINT_PUBLIC_validate_missing_output

The first parameter is required.  It can be either *token* or *fees*.  Anything else is an error.

The remaining parameters are optional.

The second parameter is file name **without the .py**.

The third parameter is the name of the test.

1.  To run all tests call it like this:

        ./run-test.sh token

2.  To run all tests in a file, call it like this:

        ./run-test.sh token test_token_req_handler


<a id="orgd389b14"></a>

## How To Contribute

Please follow the guide [here](./docs/pull-request.md). 

