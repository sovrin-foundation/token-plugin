FROM sovrin/python3:0.1.0-xenial
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
    rocksdb=5.8.8 \
    && rm -rf /var/lib/apt/lists/*

COPY ../../deps .
RUN dpkg -i python3-base58_1.0.0_amd64.deb \
    && dpkg -i python3-dateutil_2.6.1_amd64.deb \
    && dpkg -i python3-distro_1.3.0_amd64.deb \
    && dpkg -i python3-intervaltree_2.1.0_amd64.deb \
    && dpkg -i python3-ioflo_1.5.4_amd64.deb \
    && dpkg -i python3-jsonpickle_0.9.6_amd64.deb \
    && dpkg -i python3-libnacl_1.6.1_amd64.deb \
    && dpkg -i python3-orderedset_2.0.3_amd64.deb \
    && dpkg -i python3-packaging_19.0_amd64.deb \
    && dpkg -i python3-portalocker_0.5.7_amd64.deb \
    && dpkg -i python3-prompt-toolkit_0.57_amd64.deb \
    && dpkg -i python3-psutil_5.6.6_amd64.deb \
    && dpkg -i python3-pygments_2.2.0_amd64.deb \
    && dpkg -i python3-pympler_0.8_amd64.deb \
    && dpkg -i python3-pyzmq_18.1.0_amd64.deb \
    && dpkg -i python3-rlp_0.5.1_amd64.deb \
    && dpkg -i python3-rocksdb_0.6.9_amd64.deb \
    && dpkg -i python3-semver_2.7.9_amd64.deb \
    && dpkg -i python3-setuptools_38.5.2_amd64.deb \
    && dpkg -i python3-sha3_0.2.1_amd64.deb \
    && dpkg -i python3-six_1.11.0_amd64.deb \
    && dpkg -i python3-sortedcontainers_1.5.7_amd64.deb \
    && dpkg -i python3-timeout-decorator_0.5.0_amd64.deb \
    && dpkg -i python3-ursa_0.1.1_amd64.deb \
    && dpkg -i rocksdb_5.8.8_amd64.deb

# libindy
# TODO: I DO REALLY THINK THAT THIS SHOULD BE CHANGED
RUN add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master" \
    && apt-get update && apt-get install -y \
    libindy=1.13.0~1420 \
    libsovtoken=1.0.2~92 \
    indy-node \
    ursa=0.3.2-2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/indy && echo "ENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" > /etc/indy/indy_config.py \
    && pip3 install -U \
    pipenv \
    setuptools==50.3.2 \
    zipp==1.2.0 \
    importlib_metadata==2.1.1 \
    importlib_resources==3.2.1

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
ENV CI_ENV_VERSION=0.22.0
