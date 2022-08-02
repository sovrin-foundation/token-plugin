FROM ubuntu:xenial

# debian packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ssh \
        python3.5 \
        python3-pip \
        python-setuptools \
    && rm -rf /var/lib/apt/lists/*

# pypi based packages
# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
RUN python3 -m pip install -U \
        'pip<10.0.0' \
        'setuptools<=50.3.2' \
        virtualenv \
        pipenv \
        plumbum \
        deb-pkg-tools \
    && pip3 list

# user
ARG u_id=1000
ARG u_name=user

RUN if [ "$u_id" != "0" ]; then \
        useradd -ms /bin/bash -u $u_id $u_name; \
    fi
