import pytest

import os
import logging
from plenum.server.plugin.token.test.demo import mute
from plenum.server.plugin.token.test.demo import demo_logger


class Plugin:

    def _mute_output(self):
        unmuters = (mute.mute_loggers(protected=['demo_logger']), mute.mute_print())
        self._unmute_output = lambda: [f() for f in unmuters]


    def pytest_load_initial_conftests(self):
        print('Muting output')
        self._mute_output()


    def pytest_unconfigure(self):
        self._unmute_output()
        print('Unmuted output')


def run_demo(test_file):
    env_indy_path = 'INDY_PLENUM_PATH'

    try:
        indy_plenum_path = os.environ[env_indy_path]
    except KeyError:
        dl = demo_logger.DemoLogger()
        dl.log("{} environment variable needs to be set".format(env_indy_path), log_level=logging.ERROR)

    path_test_file = os.path.join(indy_plenum_path, test_file)

    os.environ['OUTPUT_NOT_CAPTURED'] = '1'
    args = ['-s', '--color', 'yes', path_test_file]

    pytest.main(args, plugins=[Plugin()])