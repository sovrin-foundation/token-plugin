import logging
from . import mute
# from colors import color

class DemoLogger():

    def __init__(self):
        self._log_name = 'demo_logger'
        self._log_level = logging.INFO
        self._logger = logging.getLogger(self._log_name)
        self.unmute_loggers = mute.mute_loggers(protected=[self._log_name])
        self.unmute_print = mute.mute_print()

    def unmute(self):
        self.unmute_loggers()
        self.unmute_print()

    def log(self, msg, **kwargs):
        # colored_msg = color("\n" + str(msg), **kwargs)
        self._logger.log(self._log_level, msg)

    def log_green(self, msg):
        self.log(msg, fg='green')

    def log_blue(self, msg):
        self.log(msg, fg='blue')