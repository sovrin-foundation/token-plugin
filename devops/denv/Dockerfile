FROM steptan/ubuntu-1604-rockdb-5.13.3-sharedlib 

ARG INDY_NODE_VERSION
ARG POOL_IP

USER root

RUN apt-get update -y && apt-get install -y \
        apt-transport-https \
        ca-certificates

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88

RUN echo "deb https://repo.sovrin.org/sdk/deb xenial stable" >> /etc/apt/sources.list

RUN apt-get update -y && apt-get install -y \
    # common stuff
        git \
        wget \
        unzip \
        python3.5 \
        python3-pip \
        python-setuptools \
        python3-venv \
        vim \
        sudo \
    # fpm
        ruby \
        ruby-dev \
        rubygems \
        gcc \
        make \
    # rocksdb python wrapper
        libgflags-dev \
        libbz2-dev \
        libzstd-dev \
        zlib1g-dev \
        liblz4-dev \
        libsnappy-dev \
    # libindy 
        python3-nacl \
        libindy-crypto=0.4.5 \
        libindy=1.6.7 \
        #//python3-indy-crypto

RUN pip3 install -U \
    setuptools \
    'pip<10.0.0' \
    setuptools \
    pytest \
    pytest-xdist \
    python3-indy==1.6.7 \
    mock

RUN useradd -m -d /home/indy -s /bin/bash -p $(openssl passwd -1 "token") -u 1000 indy; usermod -aG sudo indy

WORKDIR /home/indy

# indy-node along with supervisor
ENV INDY_NODE_VERSION ${INDY_NODE_VERSION:-1.6.79}
ARG indy_plenum_ver=1.6.54
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
RUN echo "deb https://repo.sovrin.org/deb xenial rc" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
	    supervisor \
        python3-indy-crypto=0.4.5 \
        indy-plenum=${indy_plenum_ver} \
        indy-node=${INDY_NODE_VERSION} \
    && rm -rf /var/lib/apt/lists/*
COPY supervisord.conf /etc/supervisord.conf
# config indy pool
ENV POOL_IP ${POOL_IP:-127.0.0.1}
USER indy
RUN awk '{if (index($1, "NETWORK_NAME") != 0) {print("NETWORK_NAME = \"sandbox\"")} else print($0)}' /etc/indy/indy_config.py> /tmp/indy_config.py \
    && mv /tmp/indy_config.py /etc/indy/indy_config.py \
    && generate_indy_pool_transactions --nodes 4 --clients 5 --nodeNum 1 2 3 4 --ips="$POOL_IP,$POOL_IP,$POOL_IP,$POOL_IP" \
    && chmod -R a+rw /var/lib/indy /var/log/indy /etc/indy

EXPOSE 9701 9702 9703 9704 9705 9706 9707 9708

CMD ["/usr/bin/supervisord"]
