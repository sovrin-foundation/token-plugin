#!/bin/bash

echo setting up the enviroment

sudo apt-get update
sudo apt-get update -y && apt-get install -y \
        apt-transport-https \
        ca-certificates

sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88

echo "deb https://repo.sovrin.org/sdk/deb xenial master" >> /etc/apt/sources.list

echo common stuff
sudo apt-get update -y && apt-get install -y \
        git \
        wget \
        unzip \
        python3.5 \
        python3-pip \
        python-setuptools \
        python3-venv \
        vim \
        sudo

echo fpm
sudo apt-get update -y && apt-get install -y \
        ruby \
        ruby-dev \
        rubygems \
        gcc \
        make

echo rocksdb python wrapper
sudo apt-get update -y && apt-get install -y \
        libgflags-dev \
        libbz2-dev \
        libzstd-dev \
        zlib1g-dev \
        liblz4-dev \
        libsnappy-dev

echo libindy
sudo apt-get update -y && apt-get install -y \
        python3-nacl \
        libindy-crypto=0.4.1~46 \
        libindy=1.4.0~586

echo python
sudo pip3 install -U \
    setuptools \
    'pip<10.0.0' \
    setuptools \
    pytest \
    pytest-xdist \
    python3-indy==1.4.0-dev-586 \
    mock

echo rocksdb
CWD=$(pwd)
cd /home/vagrant/
git clone https://github.com/facebook/rocksdb.git
cd rocksdb/
make all
cd $CWD

echo pycharm
tar xvzf /vagrant-common/pycharm-community.tar.gz -C /tmp
mv /tmp/pycharm-community-2018.2 /home/vagrant/pycharm

# echo UI
# sudo apt-get install -y xfce4

# these next commands do not work but it would be nice to have this working
# sudo ln -s /home/vagrant/pycharm/bin/pycharm.sh /home/vagrant/Desktop/PyCharm
# sudo chmod +x /home/vagrant/Desktop/PyCharm

# sleep 30s
echo done
# sudo shutdown -r now
