ARG VARIANT="focal"
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}

RUN apt-get update -y \
    && echo "deb http://security.ubuntu.com/ubuntu bionic main"  >> /etc/apt/sources.list \
    && apt-get install -y --allow-downgrades \
    # common stuff
    git \
    wget \
    apt-transport-https \
    ca-certificates \
    apt-utils \
    nano \
    software-properties-common \
    supervisor \ 
    # Python
    python3-pip \
    python3-nacl \
    # rocksdb python wrapper
    rocksdb-tools \
    librocksdb5.17 \
    librocksdb-dev \
    libsnappy-dev \
    liblz4-dev \
    libbz2-dev \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# fails when executed in one command with other pip install packages
# RUN pip install python-rocksdb

RUN echo "deb http://security.ubuntu.com/ubuntu bionic-security main"  >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \ 
    libssl1.0.0 \
    libssl1.1
# Indy Node and Plenum
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && echo "deb https://repo.sovrin.org/deb bionic master" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y \ 
    ursa
# install fpm
ENV FPM_VERSION=1.9.3
RUN apt-get update \
    && apt-add-repository ppa:brightbox/ruby-ng \
    && apt-get install -y --no-install-recommends \
    ruby2.6 \
    ruby2.6-dev \
    && gem install --no-document rake fpm:$FPM_VERSION \
    && rm -rf /var/lib/apt/lists/*

# Need to move libursa.so to parent dir
RUN mv /usr/lib/ursa/* /usr/lib && rm -rf /usr/lib/ursa

# Indy SDK
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 || \
# 	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys CE7709D068DB5E88 && \
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88 \ 
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9692C00E657DDE61 \ 
    && echo "deb https://hyperledger.jfrog.io/artifactory/indy focal dev" >> /etc/apt/sources.list \
    && echo "deb https://repo.sovrin.org/sdk/deb xenial master"  >> /etc/apt/sources.list \
    && echo "deb https://repo.sovrin.org/sdk/deb bionic master"  >> /etc/apt/sources.list \
    && echo "deb http://archive.ubuntu.com/ubuntu xenial universe main"  >> /etc/apt/sources.list \
    && echo "deb https://repo.sovrin.org/deb xenial master"  >> /etc/apt/sources.list \
    && apt-get update -y && apt-get install -y \ 
    libindy=1.15.0~1625-bionic \
    indy-plenum=1.13.0.dev.0 \
    indy-node=1.13.0.dev.0 \
    libsodium23

# pypi based packages
RUN pip3 install -U \ 
    Pygments==2.2.0 \
    Pympler==0.8 \
    PyNaCl==1.3.0 \
    apipkg==1.5 \
    attrs==20.3.0 \
    base58==2.1.0 \
    distro==1.5.0 \
    execnet==1.8.0 \
    flake8==3.8.4 \
    iniconfig==1.1.1 \
    intervaltree==2.1.0 \
    ioflo==2.0.2 \
    jsonpickle==2.0.0 \
    leveldb==0.201 \
    libnacl==1.7.2 \
    mccabe==0.6.1 \
    msgpack-python==0.5.6 \
    orderedset==2.0.3 \
    packaging==20.9 \
    pip==9.0.3 \
    pluggy==0.13.1 \
    portalocker==2.2.1 \
    prompt-toolkit==3.0.16 \
    psutil==5.6.6 \
    py==1.10.0 \
    pycodestyle==2.6.0 \
    pyflakes==2.2.0 \
    pyparsing==2.4.7 \
    pytest==6.2.2 \
    pytest-asyncio==0.14.0 \
    pytest-forked==1.3.0 \
    pytest-runner==5.3.0 \
    pytest-xdist==2.2.1 \
    python-dateutil==2.6.1 \
    python-rocksdb==0.7.0 \
    python-ursa==0.1.1 \
    python3-indy==1.15.0-dev-1625 \
    pyzmq==18.1.0 \
    rlp==0.6.0 \
    semver==2.13.0 \
    setuptools==53.0.0 \
    sha3==0.2.1 \
    six==1.15.0 \
    sortedcontainers==1.5.7 \
    timeout-decorator==0.5.0 \
    toml==0.10.2 \
    ujson==1.33 \
    wcwidth==0.2.5 \
    wheel==0.34.2 \
    zipp==1.2.0 \
    mock
# virtualenv \
# python-rocksdb==0.7

RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py

RUN apt-get -y autoremove

