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

tests_require = ['attrs==19.1.0', 'pytest==4.6.2', 'pytest-xdist', 'mock', 'python3-indy==1.12.0-dev-1365']

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

    install_requires=['indy-node==1.12.0'],

    setup_requires=['pytest-runner'],
    extras_require={
        'test': tests_require,
        'benchmark': ['pympler']
    },
    tests_require=tests_require,
    scripts=[]
)
