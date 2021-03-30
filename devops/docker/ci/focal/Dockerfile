FROM sovrin/python3:0.2.0-focal
# TODO LABEL maintainer="Name <email-address>"

ARG u_id=1000
ARG u_name=user

# rocksdb
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/deb xenial rc master" \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master" \
    && add-apt-repository "deb http://archive.ubuntu.com/ubuntu xenial universe main" \
    && add-apt-repository "deb http://archive.ubuntu.com/ubuntu groovy universe main" \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master" \
    && apt-get update && apt-get install -y --allow-downgrades \
    libsnappy-dev \
    python3-pip \
    python3-nacl \
    # rocksdb python wrapper
    rocksdb-tools \
    librocksdb5.17 \
    librocksdb-dev \
    libsnappy-dev \
    liblz4-dev \
    zlib1g-dev \
    libbz2-dev \
    libsodium18 \
    libsodium23 \
    python3-py=1.9.0-1 \
    supervisor \
    at \
    iptables \
    libc6=2.32-0ubuntu3 \
    && rm -rf /var/lib/apt/lists/*

RUN echo "deb http://security.ubuntu.com/ubuntu bionic-security main"  >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \ 
    libssl1.0.0

# Indy Node and Plenum
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 && \
    echo "deb https://repo.sovrin.org/deb bionic master" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \ 
    ursa=0.3.2-1


# Need to move libursa.so to parent dir
RUN mv /usr/lib/ursa/* /usr/lib && rm -rf /usr/lib/ursa

# libsovtoken
# TODO: I DO REALLY THINK THAT THIS SHOULD BE CHANGED
RUN apt-get update && apt-get install -y \
    libindy=1.13.0~1420 \
    libsovtoken=1.0.2~92 

# pypi based packages
RUN pip3 install -U \ 
    'pip<10.0.0' \
    python-ursa==0.1.1 

COPY ./deps .
RUN dpkg -i python3-base58_2.1.0_amd64.deb \
    && dpkg -i python3-dateutil_2.8.1_amd64.deb \
    && dpkg -i python3-sortedcontainers_1.5.7_amd64.deb \
    && dpkg -i python3-intervaltree_2.1.0_amd64.deb \
    && dpkg -i python3-ioflo_2.0.2_amd64.deb \
    && dpkg -i python3-jsonpickle_2.0.0_amd64.deb \
    && dpkg -i python3-libnacl_1.7.2_amd64.deb \
    && dpkg -i python3-orderedset_2.0.3_amd64.deb \
    && dpkg -i python3-pyparsing_2.0.2_amd64.deb \
    && dpkg -i python3-packaging_20.9_amd64.deb \
    && dpkg -i python3-portalocker_2.2.1_amd64.deb \
    && dpkg -i python3-wcwidth_0.2.5_amd64.deb \
    && dpkg -i python3-prompt-toolkit_3.0.16_amd64.deb \
    && dpkg -i python3-psutil_5.6.6_amd64.deb \
    && dpkg -i python3-pygments_2.2.0_amd64.deb \
    && dpkg -i python3-pympler_0.8_amd64.deb \
    && dpkg -i python3-pyzmq_18.1.0_amd64.deb \
    && dpkg -i python3-rlp_0.5.1_amd64.deb \
    && dpkg -i python3-semver_2.13.0_amd64.deb \
    && dpkg -i python3-sha3_0.2.1_amd64.deb \
    && dpkg -i python3-six_1.15.0_amd64.deb \
    && dpkg -i python3-rocksdb_0.7.0_amd64.deb \
    && dpkg -i python3-leveldb_0.201_amd64.deb \
    && dpkg -i python3-msgpack-python_0.5.6_amd64.deb \
    && dpkg -i python3-ujson_1.33_amd64.deb \
    #plenum transitive deps
    # && dpkg -i python3-setuptools_38.5.2_amd64.deb \
    # && dpkg -i python3-distro_1.3.0_amd64.deb \
    # && dpkg -i python3-iniconfig_1.1.1_amd64.deb \
    # && dpkg -i python3-toml_0.10.2_amd64.deb \
    # && dpkg -i python3-pluggy_0.13.1_amd64.deb \
    # && dpkg -i python3-attrs_19.2.0_amd64.deb \
    # && dpkg -i python3-pytest_6.2.2_amd64.deb \
    # && dpkg -i python3-ursa_0.1.1_amd64.deb \
    #indy-node deps
    && dpkg -i python3-distro_1.5.0_amd64.deb \
    && dpkg -i python3-timeout-decorator_0.5.0_amd64.deb \
    #token deps
    && dpkg -i --force-overwrite indy-plenum_9.9.9_amd64.deb \
    && dpkg -i --force-overwrite indy-node_9.9.9_amd64.deb



RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py

RUN apt-get -y autoremove
RUN rm -rf /var/lib/apt/lists/*

# TODO CMD ENTRYPOINT ...
ENV CI_ENV_VERSION=0.21.0
