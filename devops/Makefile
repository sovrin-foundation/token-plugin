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

ifeq ($(filter $(SRC_DIR_NAME),sovtoken sovtokenfees),)
$(error "SRC_DIR_NAME should be either 'sovtoken' or 'sovtokenfees' but is '$(SRC_DIR_NAME)'")
endif

SRC_MODULE_NAME ?= $(SRC_DIR_NAME)
SRC_DIR := $(PROJECT_DIR)/$(SRC_DIR_NAME)
SRC_METADATA := $(SRC_DIR)/$(SRC_MODULE_NAME)/__metadata__.py

BUILD_DIR := _build/$(SRC_DIR_NAME)

metadata_value = $(call check_non_empty,$(shell python -c "md={}; exec(open('$(SRC_METADATA)', 'r').read(), md); print(md['$1'])"), \
				   "Metadata value for '$(1)' not found in $(SRC_METADATA)")

# package related variables
PRE_PACKAGE_GOALS := pre_package
FPM_P_INPUT_TYPE := python
FPM_P_ARCH := amd64
# TODO seems fpm ignores maintainer field in setup.py
# TODO delayed (recursive) expansion since 'check_non_empty' is available only after
# ext/Makefile include statement
FPM_P_MAINTAINER = $(call metadata_value,__maintainer__)
FPM_P_OUTPUT_DIR := $(BUILD_DIR)

FPM_ARGS := --no-python-fix-name \
		   --python-bin "/usr/bin/python3" \
		   --no-python-fix-dependencies \
		   --exclude "*.pyc" \
		   --exclude "*.pyo" \
		   --after-install "build-scripts/$(OSNAME)/$(SRC_DIR_NAME)/postinst" \
           --before-remove "build-scripts/$(OSNAME)/$(SRC_DIR_NAME)/prerm" \
		   $(SRC_DIR)

ifeq ($(SRC_DIR_NAME),sovtoken)
# TODO duplication with setup.py
# necessary since indy-plenum from master is published as:
# 	pypi: indy-plenum-dev
# 	apt: indy-plenum (master component)
# remove that once sovtoken starts using indy-plenum from stable:
# 	pypi: indy-plenum
# 	apt: indy-plenum (stable component)

FPM_P_DEPENDS := indy-node(>=1.7.0~dev893)
FPM_ARGS := --no-python-dependencies $(FPM_ARGS)
endif

# docker related variables
DOCKER_NAME ?= sovrin/plugin
DOCKER_TAG ?=
CI_DOCKERFILE_PATH = docker/ci/$(OSNAME)/Dockerfile

# pytest related variables
PYTEST_ARGS ?= --showlocals

EXPORT_ENV += OSNAME SRC_DIR_NAME PYTEST_ARGS

.PHONY: all python_version test pre_package clean_pycache clean

all: test_dry test package

include ext/Makefile

export OSNAME

src_version:
	echo $(call metadata_value,__version__)

image_ci_base_version:
	$(eval PYTHON3_DOCKER_VERSION=$(call docker_from_version,'sovrin/python3',$(CI_DOCKERFILE_PATH)))
	echo $(PYTHON3_DOCKER_VERSION)

image_ci_version:
	echo $(call docker_env_value,'CI_ENV_VERSION',$(CI_DOCKERFILE_PATH))

image_ci: image_ci_base_version image_python3
ifeq ($(DOCKER_TAG),)
	$(eval DOCKER_TAG=$(call docker_env_value,'CI_ENV_VERSION',$(CI_DOCKERFILE_PATH))-$(OSNAME)-ci)
endif
	OSNAME=$(OSNAME) \
	DOCKER_UID=$(DOCKER_UID) \
	CI_DOCKER_NAME=$(DOCKER_NAME) \
	CI_DOCKER_TAG=$(DOCKER_TAG) \
		docker-compose -f docker/docker-compose.yml build ci

CI_IMAGE_BASED_TARGETS = test package clean

$(patsubst %,image_%, $(CI_IMAGE_BASED_TARGETS)): image_ci

pipenv_version:
	pipenv --version

# TODO
# clean_pycache needs only when mixing in-docker and host testing
# needs to optimze to leave cache otherwise
test: $(SRC_DIR) pipenv_version clean_pycache
	echo "Running tests"
# TODO improve usage of pipenv (remove pip completely)
# seems pipenv has some bugs regarding extras
	cd $< \
		&& pipenv --three \
		&& pipenv run pip install -U -e ../sovtoken \
		&& pipenv run pip install -U -e ../sovtokenfees \
		&& pipenv run pip install .[test] \
		&& pipenv run python -m pytest $(PYTEST_ARGS)

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
