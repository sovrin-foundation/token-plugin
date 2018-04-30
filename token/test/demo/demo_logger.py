import os
import logging
import py._io.terminalwriter as terminalwriter

class DemoLogger():

    def __init__(self, allow_colors=False):
        self._indent = 0
        self._log_name = 'demo_logger'
        self._logger = logging.getLogger(self._log_name)
        if 'OUTPUT_NOT_CAPTURED' in os.environ and int(os.environ['OUTPUT_NOT_CAPTURED']):
            self._tw = terminalwriter.TerminalWriter()
            self._tw.hasmarkup = True

    def log(self, msg, log_level = logging.DEBUG, color=None):
        msg = str(msg).strip()
        if color and hasattr(self, '_tw'):
            msg = ' ' * self._indent + msg
            msg = self._tw.markup(msg, **{color: 1})
        self._logger.log(log_level, msg)

    def log_green(self, msg):
        self.log(msg, color='green')

    def log_blue(self, msg):
        self.log(msg, color='blue')

    def log_yellow(self, msg):
        self.log(msg, color='yellow')

    def log_header(self, msg):
        self.set_indent(0)
        self.log("")
        self.log_green(msg)
        self.set_indent(2)

    def set_indent(self, number_of_spaces):
        self._indent = number_of_spaces
