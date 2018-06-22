import os
import sys
import plenum.server.plugin.sovtoken.metadata_helper as helper

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

METADATA = os.path.join(SETUP_DIRNAME, 'metadata.json')

tests_require = ['pytest', 'pytest-xdist', 'python3-indy']

with open(METADATA) as d:
    md = helper.get_metadata(d.read(), ["version", "author", "license"])

setup(

    name='sovtoken',
    version= md["version"],
    # TODO: Change the field values below
    description='Plenum Byzantine Fault Tolerant Protocol',
    long_description='Plenum Byzantine Fault Tolerant Protocol',
    url='https://github.com/hyperledger/indy-plenum',
    download_url='https://github.com/hyperledger/indy-plenum/tarball/{}'.
        format( md["version"]),
    author= md["author"],
    author_email='hyperledger-indy@lists.hyperledger.org',
    license= md["license"],
    keywords='Byzantine Fault Tolerant Plenum',
    packages=find_packages(exclude=['test', 'test.*', 'docs', 'docs*']) + [
        'data', ],
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.json', '*.conf', '*.html',
             '*.css', '*.ico', '*.png', 'LICENSE', 'LEGAL', 'src']},
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

