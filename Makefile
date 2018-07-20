SHELL := /usr/bin/env bash

setup: 
	docker exec -u 0 -ti plugin_token_1 /bin/bash -c 'bash install_payment_plugins.sh' 

test: 
	docker exec -u 0 -ti plugin_token_1 /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/' 

start:
	docker-sync-stack start 

clean:
	docker-sync-stack clean

