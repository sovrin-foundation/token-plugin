import os
import sys

from setuptools import setup, find_packages

v = sys.version_info
if sys.version_info < (3, 5):
    msg = "FAIL: Requires Python 3.5 or later, " \
          "but setup.py was run using {}.{}.{}"
    v = sys.version_info
    print(msg.format(v.major, v.minor, v.micro))
    # noinspection PyPackageRequirements
    print("NOTE: Installation failed. Run setup.py using python3")
    sys.exit(1)

# Change to ioflo's source directory prior to running any command
try:
    SETUP_DIRNAME = os.path.dirname(__file__)
except NameError:
    # We're probably being frozen, and __file__ triggered this NameError
    # Work around this
    SETUP_DIRNAME = os.path.dirname(sys.argv[0])

if SETUP_DIRNAME != '':
    os.chdir(SETUP_DIRNAME)

SETUP_DIRNAME = os.path.abspath(SETUP_DIRNAME)

METADATA = os.path.join(SETUP_DIRNAME, 'plugin', '__metadata__.py')
# Load the metadata using exec() so we don't trigger an import of ioflo.__init__
exec(compile(open(METADATA).read(), METADATA, 'exec'))

tests_require = ['pytest', 'pytest-xdist', 'python3-indy']

setup(
    name='sovrin-plugin',
    version=__version__,
    # TODO: Change the field values below
    description='Plenum Byzantine Fault Tolerant Protocol',
    long_description='Plenum Byzantine Fault Tolerant Protocol',
    url='https://github.com/hyperledger/indy-plenum',
    download_url='https://github.com/hyperledger/indy-plenum/tarball/{}'.
        format(__version__),
    author=__author__,
    author_email='hyperledger-indy@lists.hyperledger.org',
    license=__license__,
    keywords='Byzantine Fault Tolerant Plenum',
    packages=find_packages(exclude=['test', 'test.*', 'docs', 'docs*']) + [
        'data', ],
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.json', '*.conf', '*.html',
             '*.css', '*.ico', '*.png', 'LICENSE', 'LEGAL', 'token']},
    include_package_data=True,
    install_requires=['indy-plenum-dev==1.2.242',],
    setup_requires=['pytest-runner'],
    extras_require={
        'tests': tests_require,
        'benchmark': ['pympler']
    },
    tests_require=tests_require,
    scripts=[]
)
