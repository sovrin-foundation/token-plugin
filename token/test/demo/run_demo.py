import os

import pytest

from plenum.server.plugin.token.test.demo import mute


class Plugin():

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
    indy_plenum_path = os.environ['INDY_PLENUM_PATH']
    path_test_file = os.path.join(indy_plenum_path, test_file)

    os.environ['OUTPUT_NOT_CAPTURED'] = '1'
    args = ['-s', '--color', 'yes', path_test_file]

    pytest.main(args, plugins=[Plugin()])