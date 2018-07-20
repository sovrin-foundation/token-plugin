SHELL := /usr/bin/env bash
pwd = $(shell pwd)
dirname = $(shell basename ${pwd})

setup: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'bash install_payment_plugins.sh' 

test: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/' 

start:
	docker-sync-stack start 

clean:
	docker-sync-stack clean

