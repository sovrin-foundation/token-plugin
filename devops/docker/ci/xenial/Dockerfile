FROM hyperledger/indy-core-baseci:0.0.3-master
# TODO LABEL maintainer="Name <email-address>"

ARG u_id=1000
ARG u_name=user

# TODO move to base image
RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# rocksdb
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/deb xenial rc master" \
    && apt-get update && apt-get install -y \
    libbz2-dev \
    zlib1g-dev \
    liblz4-dev \
    libsnappy-dev \
    rocksdb=5.8.8 \
    && rm -rf /var/lib/apt/lists/*

# libindy
# TODO: I DO REALLY THINK THAT THIS SHOULD BE CHANGED
RUN add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master" \
    && apt-get update && apt-get install -y \
    libindy=1.13.0~1420 \
    libsovtoken=1.0.2~92 \
    ursa=0.3.2-2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py \
    && pip3 install -U \
    setuptools==50.3.2 \
    zipp==1.2.0 \
    pytest==4.6.2 \
    pytest-xdist==2.2.1 \
    importlib_metadata==2.1.1 \
    importlib_resources==3.2.1 \
    python3-indy==1.13.0-dev-1420 \
    indy-node==1.13.0.dev1225 \
    mock==3.0.5


# TODO CMD ENTRYPOINT ...
ENV CI_ENV_VERSION=0.22.0
