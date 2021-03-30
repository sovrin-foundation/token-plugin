#TODO
# - docker-compose re-runs build always (it's fast because of cache but anyway)

OSNAME ?= focal

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

ifeq ($(SRC_DIR_NAME),sovtoken)
# TODO duplication with setup.py
# necessary since indy-plenum from master is published as:
# 	pypi: indy-plenum-dev
# 	apt: indy-plenum (master component)
# remove that once sovtoken starts using indy-plenum from stable:
# 	pypi: indy-plenum
# 	apt: indy-plenum (stable component)

FPM_P_DEPENDS := indy-node(=1.13.0~dev1225)
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

xenial:
	$(eval OSNAME = xenial)
# this explicitly will build a 16.04 release (xenial). alternatively make <target> <OSNAME>= can be used, (currently focal and xenial are supported).
image_ci_xenial: xenial image_ci

pipenv_version:
	pipenv --version

# TODO
# clean_pycache needs only when mixing in-docker and host testing
# needs to optimze to leave cache otherwise
test: $(SRC_DIR)
	echo "Running tests"
# TODO improve usage of pipenv (remove pip completely)
# seems pipenv has some bugs regarding extras
	cd $< \
		&& pipenv --python 3.5 \
		&& pipenv run pip install -U -e ../sovtoken \
		&& pipenv run pip install -U -e ../sovtokenfees \
		&& pipenv run pip install .[test] \
		&& pipenv run python -m pytest $(PYTEST_ARGS)

pre_package: python_version | $(BUILD_DIR)
	rm -f $(BUILD_DIR)/$(LIBNAME)*.$(FPM_P_OUTPUT_TYPE)
	rm -rf $(SRC_DIR)/build


$(BUILD_DIR):
	mkdir -p $@

test_local_aws: image_ci
	pushd .. \
	&& docker pull amazon/aws-codebuild-local:latest --disable-content-trust=false \
	&& ./codebuild_build.sh -i sovrin/plugin:0.21.0-$(OSNAME)-ci -b ./devops/aws-codebuild/buildspec.yml -a ./tmp -e aws_local_codebuild_sovtoken.env \
	&& ./codebuild_build.sh -i sovrin/plugin:0.21.0-$(OSNAME)-ci -b ./devops/aws-codebuild/buildspec.yml -a ./tmp -e aws_local_codebuild_sovtokenfees.env \
	&& popd
	

clean_pycache:
	find $(SRC_DIR) \
		-name '__pycache__' -delete -print \
		-o \
		-name '*.pyc' -delete -print

clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(SRC_DIR)/build
