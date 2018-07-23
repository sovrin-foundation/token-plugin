echo -e "\nENABLED_PLUGINS = ['sovtoken', 'sovtokenfees']" >> /etc/indy/indy_config.py
pip install -U -e sovtoken/
pip install -U -e sovtokenfees/
