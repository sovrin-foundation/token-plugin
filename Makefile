SHELL := /usr/bin/env bash
pwd = $(shell pwd)
dirname = $(shell basename ${pwd})

setup: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'bash -x install_payment_plugins.sh'

test: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtoken/ && pytest sovtoken/test/'

test_fees:	
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'cd sovtokenfees/ && pytest sovtokenfees/test/'

start:
	docker-sync-stack start
deps: 
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'sed s/msgpack==0.4.6-1build1/python-msgpack==0.4.6/ /usr/local/lib/python3.5/dist-packages/indy_plenum-1.6.51-py3.5.egg-info/requires.txt > /usr/local/lib/python3.5/dist-packages/indy_plenum-1.6.51-py3.5.egg-info/requires.txt'
	docker exec -u 0 -ti ${dirname:=_token_1} /bin/bash -c 'sed s/ujson==1.33-1build1/ujson==1.33/ /usr/local/lib/python3.5/dist-packages/indy_plenum-1.6.51-py3.5.egg-info/requires.txt > /usr/local/lib/python3.5/dist-packages/indy_plenum-1.6.51-py3.5.egg-info/requires.txt '
clean:
	docker-sync-stack clean

