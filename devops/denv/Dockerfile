FROM steptan/ubuntu-1604-rockdb-5.13.3-sharedlib 

ARG INDY_NODE_VERSION
ARG POOL_IP

USER root

RUN apt-get update -y && apt-get install -y \
    apt-transport-https \
    ca-certificates

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys BD33704C
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
RUN echo "deb http://us.archive.ubuntu.com/ubuntu xenial main universe" >> /etc/apt/sources.list
RUN echo "deb https://repo.sovrin.org/deb xenial master" >> /etc/apt/sources.list
RUN echo "deb https://repo.sovrin.org/sdk/deb xenial master" >> /etc/apt/sources.list
RUN echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu xenial main" >> /etc/apt/sources.list

RUN apt-get update -y && apt-get install -y \
    # common stuff
    git \
    wget \
    unzip \
    python3 \
    python3-pip \
    python-setuptools \
    python3-venv \
    vim \
    sudo \
    ursa \
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
    libindy \
    indy-cli \
    libsovtoken=1.0.2~92
#//python3-indy-crypto

RUN pip3 install -U \
    setuptools==50.3.2 \
    pytest==4.6.2 \
    zipp==1.0.0 \
    importlib_metadata==2.1.1 \
    pytest-xdist==2.2.1 \
    python3-indy==1.16.0 \
    mock==3.0.5

RUN useradd -m -d /home/indy -s /bin/bash -p $(openssl passwd -1 "token") -u 1000 indy; usermod -aG sudo indy
RUN ln -s /usr/bin/pip3 /usr/bin/pip

WORKDIR /home/indy

# indy-node along with supervisor
ENV INDY_NODE_VERSION ${INDY_NODE_VERSION:-1.13.0~dev1225}
ARG indy_plenum_ver=1.13.0~dev1033
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88
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
