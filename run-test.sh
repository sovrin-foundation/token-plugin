#!/bin/bash
echo

if [ "$1" == "--help" ]; then
    echo
    echo runs plenum plugin tests hosted in docker image
    echo run-test.sh plugin-name file-name test-name
    echo -e '\teg: run-test.sh token test_token_req_handler test_token_req_handler_MINT_PUBLIC_validate_missing_output'
    echo
    echo -e '\tplugin-name      must be either token or fees'
    echo -e '\tfile-name        file name with no extension (aka no .py) (optional)'
    echo -e '\ttest-name        name of the test (optional)'
    echo
    exit
fi


DIR_NAME=${PWD##*/}
DOCKER_IMAGE=${DIR_NAME}_token_1

# defaults are nothing.
PYTHON_WORKING_DIR=
PYTHON_FILE_NAME=
PYTHON_TEST_NAME=
PYTHON_TEST_PATH=
PYTHON_TEST_COMMAND_PARAM=
PYTHON_COMMAND=

# eval $1:  it must be either token or fees
if [ "$1" != "token" ] && [ "$1" != "fees" ]; then
    echo parameter 1 must be either 'token' or 'fees'
    echo
    exit
fi

if [ "$1" == "token" ]; then
    PYTHON_WORKING_DIR=sovtoken
    PYTHON_TEST_PATH=${PYTHON_WORKING_DIR}/test/
elif [ "$1" == "fees" ]; then
    PYTHON_WORKING_DIR=sovtokenfees
    PYTHON_TEST_PATH=${PYTHON_WORKING_DIR}/test/
fi

# eval $2 (optional)   expectation is if this parameter is included it will be a python file name (sans .py).
if [ "$2" != "" ]; then
    PYTHON_FILE_NAME=$(echo "$2" | cut -f 1 -d '.')

    # eval $3 (also optional)....expectation is this will be a test name (aka function name starting with
    # "test" since that's how pytest works)
    if [ "$3" != "" ]; then
        echo configuring for running individual test
        PYTHON_TEST_NAME=$3
        PYTHON_TEST_COMMAND_PARAM=${PYTHON_TEST_PATH}${PYTHON_FILE_NAME}.py::${PYTHON_TEST_NAME}
    else
        echo configuring for running all tests in file
        PYTHON_TEST_COMMAND_PARAM=${PYTHON_TEST_PATH}${PYTHON_FILE_NAME}.py
    fi

    PYTHON_COMMAND="docker exec -u 0 -ti ${DOCKER_IMAGE} /bin/bash -c 'cd ${PYTHON_WORKING_DIR}/ && pytest ${PYTHON_TEST_COMMAND_PARAM}'"
else
    echo configuring to run all tests
    PYTHON_COMMAND="docker exec -u 0 -ti ${DOCKER_IMAGE} /bin/bash -c 'cd ${PYTHON_WORKING_DIR}/ && pytest'"
fi

echo
echo DOCKER_IMAGE = $DOCKER_IMAGE
echo PYTHON_TEST_PATH = $PYTHON_TEST_PATH
echo PYTHON_FILE_NAME = $PYTHON_FILE_NAME
echo PYTHON_TEST_NAME = $PYTHON_TEST_NAME
echo PYTHON_COMMAND = $PYTHON_COMMAND
echo

# the command executed should look something like this
# docker exec -u 0 -ti mine_token_1 /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/test_token_req_handler.py::test_token_req_handler_MINT_PUBLIC_validate_missing_output'

eval $PYTHON_COMMAND

echo done
echo