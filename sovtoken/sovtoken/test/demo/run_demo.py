import argparse
import os

import pytest
# Have to import plenum now, because it removes all logging handlers when
# is loaded.
import plenum

from sovtoken.test.demo import demo_logger, mute


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("demo_file_path", help="The path to the demo you want to run")
    return parser.parse_args()


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


os.environ['OUTPUT_NOT_CAPTURED'] = '1'

args = parse_args()
pytest_args = [
    '-s',
    '--color',
    'yes',
    '--log-level',
    'NOTSET',
    args.demo_file_path
]
pytest.main(pytest_args, plugins=[Plugin()])
