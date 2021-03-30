#!/usr/bin/env bash
echo -e "\nENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" >> /etc/indy/indy_config.py
pip3 install -e --force sovtoken/
pip3 install -e sovtokenfees/
