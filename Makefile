SHELL := /usr/bin/env bash


setup: bundle-install pull-images pull-dependencies

setup-build: rebuild pull-dependencies

bundle-install:
	bundle install --path .bundle/gems
	