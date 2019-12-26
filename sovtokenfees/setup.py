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
metadata={}
with open(os.path.join(here, 'sovtokenfees', '__metadata__.py'), 'r') as f:
    exec(f.read(), metadata)

tests_require = ['attrs==19.1.0', 'pytest==4.6.2', 'pytest-xdist', 'python3-indy==1.13.0-dev-1404']

setup(

    name=metadata['__title__'],
    version= metadata['__version__'],
    description=metadata['__description__'],
    long_description=metadata['__long_description__'],
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    license=metadata['__license__'],
    keywords='',
    packages=find_packages(exclude=['test', 'test.*', 'docs', 'docs*']),
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.json', '*.conf', '*.html',
             '*.css', '*.ico', '*.png', 'LICENSE', 'LEGAL', 'sovtokenfees']},
    include_package_data=True,
    setup_requires=['pytest-runner'],
    install_requires=['sovtoken'],
    extras_require={
        'test': tests_require,
        'benchmark': ['pympler']
    },
    tests_require=tests_require,
    scripts=[]
)
