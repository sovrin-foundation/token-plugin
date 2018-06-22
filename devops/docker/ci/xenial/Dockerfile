FROM evernym/python3:0.1.0-xenial
# TODO LABEL maintainer="Name <email-address>"

ARG u_id=1000
ARG u_name=user

# TODO move to base image
RUN apt-get update && apt-get install -y \
        software-properties-common \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/deb xenial master" \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial stable" \
    && apt-get update && apt-get install -y \
        libbz2-dev \
        zlib1g-dev \
        liblz4-dev \
        libsnappy-dev \
        rocksdb=5.8.8 \
        libindy \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -U \
        indy-plenum-dev

RUN useradd -ms /bin/bash -u $u_id $u_name
USER $u_name

# TODO CMD ENTRYPOINT ...
WORKDIR /home/$u_name

ENV CI_ENV_VERSION=0.1.0
