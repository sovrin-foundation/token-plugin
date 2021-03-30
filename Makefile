SHELL := /usr/bin/env bash
pwd = $(shell pwd)
dirname = $(shell basename ${pwd})
setup: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'bash -x install_payment_plugins.sh'

test: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/'

test_fees:	
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtokenfees/ && pytest sovtokenfees/test/'

test_helpers:
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtokenfees/sovtokenfees/test/helpers/test && pytest --test_helpers'

start:
	pushd devops && make image_ci
	docker-sync-stack start
	popd
clean:
	docker-sync-stack clean

