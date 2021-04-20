FROM sovrin/python3:0.2.0-focal

ARG INDY_NODE_VERSION
ARG POOL_IP

USER root

RUN useradd -m -d /home/indy -s /bin/bash -p $(openssl passwd -1 "token") -u 1000 indy; usermod -aG sudo indy

WORKDIR /home/indy

# indy-node along with supervisor
ENV INDY_NODE_VERSION ${INDY_NODE_VERSION:-1.13.0~dev1225}
ARG indy_plenum_ver=1.13.0~dev1033
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && echo "deb https://repo.sovrin.org/sdk/deb xenial master" >> /etc/apt/sources.list \
    && echo "deb https://repo.sovrin.org/deb xenial stable master" >> /etc/apt/sources.list \
    && echo "deb http://archive.ubuntu.com/ubuntu/ xenial universe main" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y --allow-downgrades \
    python3-jsonpickle=0.9.6 \
    python3-ujson=1.33-1build1 \ 
    python3-prompt-toolkit=0.57-1 \ 
    python3-pygments=2.2.0 \ 
    python3-rlp=0.5.1 \ 
    python3-sha3=0.2.1 \ 
    python3-leveldb \ 
    python3-distro=1.3.0 \ 
    python3-base58=1.0.0 \ 
    python3-sortedcontainers=1.5.7 \ 
    python3-portalocker=0.5.7 \ 
    python3-libnacl=1.6.1 \ 
    python3-six=1.11.0 \ 
    python3-intervaltree=2.1.0 \ 
    python3-msgpack=0.4.6-1build1 \ 
    python3-dateutil=2.6.1 \ 
    python3-packaging=19.0 \ 
    python3=3.5.1-3 \
    python3.5-dev \ 
    python3-pip=8.1.1-2 \
    python-pip-whl=8.1.1-2 \
    python3-minimal=3.5.1-3 \
    libpython3-stdlib=3.5.1-3 \ 
    python3-setuptools=38.5.2 \
    python3-pkg-resources=20.7.0-1 \
    python3-rocksdb=0.6.9 \
    supervisor \
    indy-plenum=${indy_plenum_ver} \
    indy-node=${INDY_NODE_VERSION} \
    libindy=1.13.0~1420 \
    libsovtoken=1.0.2~92 \
    ursa=0.3.2-1 \
    && rm -rf /var/lib/apt/lists/*

# Indy SDK
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 || \
# 	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys CE7709D068DB5E88 && \
RUN echo "deb https://repo.sovrin.org/sdk/deb bionic master" >> /etc/apt/sources.list \
    && apt-get update -y && apt-get install -y \
    && libindy=1.13.0~1420 \
    && rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisord.conf
# config indy pool
ENV POOL_IP ${POOL_IP:-127.0.0.1}

RUN python3 -m pip install --upgrade pip==9.0.1 \
    setuptools==50.3.2 \
    pytest==4.6.2 \
    zipp==1.0.0 \
    importlib_metadata==2.1.1 \
    pytest-xdist==2.2.1 \
    python3-indy==1.16.0 \
    mock==3.0.5

RUN awk '{if (index($1, "NETWORK_NAME") != 0) {print("NETWORK_NAME = \"sandbox\"")} else print($0)}' /etc/indy/indy_config.py> /tmp/indy_config.py \
    && mv /tmp/indy_config.py /etc/indy/indy_config.py \
    && mv /usr/lib/ursa/* /usr/lib && rm -rf /usr/lib/ursa \
    && generate_indy_pool_transactions --nodes 4 --clients 5 --nodeNum 1 2 3 4 --ips="$POOL_IP,$POOL_IP,$POOL_IP,$POOL_IP" \
    && chmod -R a+rw /var/lib/indy /var/log/indy /etc/indy

USER indy

EXPOSE 9701 9702 9703 9704 9705 9706 9707 9708

CMD ["/usr/bin/supervisord"]
