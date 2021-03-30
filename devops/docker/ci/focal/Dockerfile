FROM sovrin/python3:0.2.0-focal
# TODO LABEL maintainer="Name <email-address>"

ARG u_id=1000
ARG u_name=user

# TODO move to base image
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# rocksdb
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/deb xenial rc master" \
    && apt-get update && apt-get install -y \
    libbz2-dev \
    zlib1g-dev \
    liblz4-dev \
    libsnappy-dev \
    python3.5-dev \
    # rocksdb python wrapper
    rocksdb-tools \
    librocksdb5.17 \
    librocksdb-dev \
    libsnappy-dev \
    liblz4-dev \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-rocksdb

RUN echo "deb http://security.ubuntu.com/ubuntu bionic-security main"  >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \ 
    libssl1.0.0

# Indy SDK
RUN echo "deb https://repo.sovrin.org/sdk/deb bionic master" >> /etc/apt/sources.list && \
    apt-get update -y && apt-get install -y \ 
    libindy=1.13.0~1420

# libsovtoken
# TODO: I DO REALLY THINK THAT THIS SHOULD BE CHANGED
RUN add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master" \
    && apt-get update && apt-get install -y \
    libsovtoken=1.0.2~92 \
    ursa=0.3.2-2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py \
    && pip3 install -U \
    pipenv \
    zipp==1.2.0 \
    importlib_metadata==2.1.1 \
    importlib_resources==3.2.1

RUN apt-get -y autoremove
RUN rm -rf /var/lib/apt/lists/*

# TODO CMD ENTRYPOINT ...
ENV CI_ENV_VERSION=0.21.0
