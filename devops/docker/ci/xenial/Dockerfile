FROM evernym/python3:0.1.0-xenial
# TODO LABEL maintainer="Name <email-address>"

ARG u_id=1000
ARG u_name=user

# TODO move to base image
RUN apt-get update && apt-get install -y \
        software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# rocksdb
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/deb xenial rc" \
    && apt-get update && apt-get install -y \
        libbz2-dev \
        zlib1g-dev \
        liblz4-dev \
        libsnappy-dev \
        rocksdb=5.8.8 \
    && rm -rf /var/lib/apt/lists/*

# libindy and libindy-crypto
# TODO: I DO REALLY THINK THAT THIS SHOULD BE CHANGED
RUN add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial rc" \
    && apt-get update && apt-get install -y \
        libindy-crypto=0.4.5 \
        libindy=1.6.7 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py \
    && pip3 install -U pipenv

# TODO workaround (suggested by http://click.pocoo.org/5/python3/)
# to use pipenv's dependency 'click' (http://click.pocoo.org)
# check for alternatives
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN if [ "$u_id" != "0" ]; then \
        useradd -ms /bin/bash -u $u_id $u_name; \
    fi
USER $u_id

# TODO CMD ENTRYPOINT ...
ENV CI_ENV_VERSION=0.9.0
