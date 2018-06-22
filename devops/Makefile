#TODO
# - docker-compose re-runs build always (it's fast because of cache but anyway)

RELEASE ?= 1
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
# TODO fix project strucure and update that
SRC_VERSION := $(shell PYTHONPATH=$(SRC_DIR) python -c "from __metadata__ import __version__; print(__version__)")

BUILD_DIR := _build

# package related variables
PRE_PACKAGE_GOALS := pre_package
FPM_P_INPUT_TYPE=python
FPM_P_MAINTAINER := Evernym
FPM_P_URL := https://github.com/evernym/plugin
FPM_P_LICENSE := Apache License 2.0
FPM_P_VENDOR := Evernym
# TODO conditional: fees or payments
FPM_P_DESCRIPTION := Sovrin Ledger plugins
FPM_P_NAME = $(SRC_DIR_NAME)
FPM_P_VERSION ?= $(SRC_VERSION)
FPM_P_OUTPUT_DIR = $(BUILD_DIR)
FPM_ARGS = --python-package-name-prefix "python3" \
		   --python-bin "/usr/bin/python3" \
		   --exclude "*.pyc" \
		   --exclude "*.pyo" \
		   $(SRC_DIR)

# docker related variables
DOCKER_NAME ?= evernym/plugin
DOCKER_TAG ?=
CI_DOCKERFILE_PATH = docker/ci/$(OSNAME)/Dockerfile

EXPORT_ENV += OSNAME

.PHONY: all python_version test pre_package clean

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

python_version:
	python --version
	pip --version
	pytest --version

test: $(SRC_DIR) python_version
	echo "Running tests"
	cd $< && python -m pytest

pre_package:
	rm -f $(BUILD_DIR)/$(LIBNAME)*$(SRC_VERSION)*.$(FPM_P_OUTPUT_TYPE)

clean:
	rm -rf $(BUILD_DIR)
