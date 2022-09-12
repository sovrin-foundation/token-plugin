import os
import sys
import json

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

try:
    here = os.path.abspath(os.path.dirname(__file__))
except NameError:
    # it can be the case when we are being run as script or frozen
    here = os.path.abspath(os.path.dirname(sys.argv[0]))

metadata = {'__file__': os.path.join(here, 'sovtoken', '__metadata__.py')}
with open(os.path.join(here, 'sovtoken', '__metadata__.py'), 'r') as f:
    exec(f.read(), metadata)

tests_require = ['pip==9.0.3', 'pytest-xdist', 'mock', 'python-rocksdb==0.6.9', 'indy-node==1.13.2.rc3']

setup(
    name=metadata['__title__'],
    version=metadata['__version__'],
    description=metadata['__description__'],
    long_description=metadata['__long_description__'],
    url=metadata['__url__'],
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    maintainer=metadata['__maintainer__'],
    license=metadata['__license__'],
    keywords='',
    packages=find_packages(exclude=['test', 'test.*', 'docs', 'docs*']),
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.json', '*.conf', '*.html',
             '*.css', '*.ico', '*.png', 'LICENSE', 'LEGAL', 'sovtoken']},
    include_package_data=True,

    install_requires=[],

    setup_requires=['pytest-runner'],
    extras_require={
        'test': tests_require,
        'benchmark': ['pympler']
    },
    tests_require=tests_require,
    scripts=[]
)
