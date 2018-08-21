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

here = os.path.abspath(os.path.dirname(__file__))

metadata = {}
with open(os.path.join(here, 'sovtoken', '__metadata__.py'), 'r') as f:
    exec(f.read(), metadata)

tests_require = ['pytest', 'pytest-xdist', 'mock', 'python3-indy==1.6.1-dev-657']

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
    # TODO change to 'indy-plenum' with proper version
    # once sovtoken starts using indy-plenum from stable
    #
    # '>=' here seems makes sense since usually indy-plenum is
    # installed as indy-node's dependency and might be with greater
    # version (just to not update each time new indy-node is released)
    install_requires=['indy-plenum-dev==1.6.510'],
    setup_requires=['pytest-runner'],
    extras_require={
        'test': tests_require,
        'benchmark': ['pympler']
    },
    tests_require=tests_require,
    scripts=[]
)
