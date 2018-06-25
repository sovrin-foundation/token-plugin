#TODO
# - docker-compose re-runs build always (it's fast because of cache but anyway)

OSNAME ?= xenial

ifndef PROJECT_DIR
PROJECT_DIR := $(shell git rev-parse --show-toplevel)
endif

# project variables
ifndef SRC_DIR_NAME
SRC_DIR_NAME := sovtoken
endif

ifeq ($(filter $(SRC_DIR_NAME),sovtoken sovtoken_fees),)
$(error "SRC_DIR_NAME should be either 'sovtoken' or 'sovtoken_fees' but is '$(SRC_DIR_NAME)'")
endif

SRC_DIR := $(PROJECT_DIR)/$(SRC_DIR_NAME)

BUILD_DIR := _build/$(SRC_DIR_NAME)

# package related variables
PRE_PACKAGE_GOALS := pre_package
FPM_P_INPUT_TYPE := python
FPM_P_ARCH := amd64
# TODO seems fpm ignores __maintainer__ field in setup.py
FPM_P_MAINTAINER := $(shell PYTHONPATH=$(SRC_DIR) python -c "from __metadata__ import __maintainer__; print(__maintainer__)")
FPM_P_OUTPUT_DIR = $(BUILD_DIR)
FPM_ARGS = --no-python-fix-name \
		   --python-bin "/usr/bin/python3" \
		   --exclude "*.pyc" \
		   --exclude "*.pyo" \
		   --after-install "build-scripts/$(OSNAME)/$(SRC_DIR_NAME)/postinst" \
           --before-remove "build-scripts/$(OSNAME)/$(SRC_DIR_NAME)/prerm" \
		   $(SRC_DIR)

# docker related variables
DOCKER_NAME ?= evernym/plugin
DOCKER_TAG ?=
CI_DOCKERFILE_PATH = docker/ci/$(OSNAME)/Dockerfile

# pytest related variables
PYTEST_ARGS ?=

PYTEST_LOCALS ?= 1
ifeq ($(PYTEST_LOCALS),1)
PYTEST_ARGS += --showlocals
endif

ifneq ($(PYTEST_JUNIT_XML),)
PYTEST_ARGS += --junit-xml=$(PYTEST_JUNIT_XML)
endif


EXPORT_ENV += OSNAME SRC_DIR_NAME PYTEST_ARGS

.PHONY: all python_version test pre_package clean_pycache clean

all: test_dry test package

include ext/Makefile

export OSNAME

image_ci_base_version:
	$(eval PYTHON3_DOCKER_VERSION=$(call docker_from_version,'evernym/python3',$(CI_DOCKERFILE_PATH)))
	echo $(PYTHON3_DOCKER_VERSION)

image_ci_version:
	echo $(call docker_env_value,'CI_ENV_VERSION',$(CI_DOCKERFILE_PATH))

image_ci: image_ci_base_version image_python3
ifeq ($(DOCKER_TAG),)
	$(eval DOCKER_TAG=$(call docker_env_value,'CI_ENV_VERSION',$(CI_DOCKERFILE_PATH))-$(OSNAME)-ci)
endif
	OSNAME=$(OSNAME) \
	CI_DOCKER_NAME=$(DOCKER_NAME) \
	CI_DOCKER_TAG=$(DOCKER_TAG) \
		docker-compose -f docker/docker-compose.yml build ci

CI_IMAGE_BASED_TARGETS = test package clean

$(patsubst %,image_%, $(CI_IMAGE_BASED_TARGETS)): image_ci

pipenv_version:
	pipenv --version

# TODO
# clean_pycache needs only when mixinf in-docker and host testing
# needs to optimze to leave cache otherwise
test: $(SRC_DIR) pipenv_version clean_pycache
	echo "Running tests"
# TODO improve usage of pipenv (remove pip completely)
# seems pipenv has some bugs regarding extras
	cd $< \
		&& pipenv --three \
		&& pipenv run pip install .[tests] \
		&& PYTHONPATH=.. pipenv run python -m pytest $(PYTEST_ARGS)

pre_package: python_version | $(BUILD_DIR)
	rm -f $(BUILD_DIR)/$(LIBNAME)*.$(FPM_P_OUTPUT_TYPE)
	rm -rf $(SRC_DIR)/build


$(BUILD_DIR):
	mkdir -p $@

clean_pycache:
	find $(SRC_DIR) \
		-name '__pycache__' -delete -print \
		-o \
		-name '*.pyc' -delete -print

clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(SRC_DIR)/build
