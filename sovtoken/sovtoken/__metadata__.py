"""
sovtoken package metadata
"""
import os
import json

METADATA_FILENAME = 'metadata.json'
METADATA_FILE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), METADATA_FILENAME)


def loadAuthor(metadata_file: str = METADATA_FILE):
    with open(metadata_file, 'r') as f:
        data = json.load(f)
        return data['author']


def loadLicense(metadata_file: str = METADATA_FILE):
    with open(metadata_file, 'r') as f:
        data = json.load(f)
        return data['license']


def loadVersion(metadata_file: str = METADATA_FILE):
    with open(metadata_file, 'r') as f:
        data = json.load(f)
        return data['version']


__author__ = loadAuthor()
__license__ = loadLicense()
__version__ = loadVersion()
__author_email__ = ''
__description__ = 'Token Plugin For Indy Plenum'

__long_description__ = ''
__maintainer__ = 'Sovrin'
__title__ = 'sovtoken'
__url__ = 'https://github.com/sovrin-foundation/token-plugin/tree/master/sovtoken'

__author_email__ = ''
__maintainer__ = "Sovrin"


__all__ = ['__title__',
           '__description__',
           '__version__',
           '__long_description__',
           '__url__',
           '__author__',
           '__author_email__',
           '__maintainer__',
           '__license__'
           ]
