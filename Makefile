SHELL := /usr/bin/env bash

it-so:
	docker exec -u 0 -ti plugin_plugin_1 /bin/bash -c 'bash install_payment_plugins.sh' 
it-so test: 
	docker exec -u 0 -ti plugin_plugin_1 /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/' 
setup: bundle-install pull-dependencies

setup-build: rebuild pull-dependencies

bundle-install:
	bundle install --path .bundle/gems

start:
	bundle exec docker-sync-stack start

start-services:
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml up

start-sync:
	bundle exec docker-sync start --foreground

clean:
	bundle exec docker-sync-stack clean

pull-images:
	docker-compose pull

push-images:
	docker-compose push

pull-dependencies:

build:
	docker-compose build
