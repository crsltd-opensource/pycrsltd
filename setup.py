#!/usr/bin/env python
"""Requires setuptools.

To build the setuptools egg use
    python setup.py bdist_egg
and either upload it to the PyPI with:
    python setup.py upload
or upload to your own server and register the release with PyPI:
    python setup.py register

A source distribution (.zip) can be built with
    python setup.py sdist --format=zip
That uses the manifest.in file for data files rather than searching for them here
"""

from setuptools import setup, Extension, find_packages
import sys
sys.path.append('src')#so we can import openpyxl
import pycrsltd#to fetch __version__ etc

setup(name = "pycrsltd",
    packages = ["pycrsltd"],
    include_package_data = True,
    package_data = {}, #DOESN'T AFFECT zip DISTRIBUTION. MUST MODIFY MANIFEST.in TOO
    #metadata
    version = pycrsltd.__version__,
    description = "A Python library to interface with CRS Ltd hardware",
    long_description = "A Python library to interface with CRS Ltd hardware",
    author = pycrsltd.__author__,
    author_email = pycrsltd.__author_email__,
    url = pycrsltd.__url__,
    license = pycrsltd.__license__,
    download_url = pycrsltd.__downloadUrl__,
    test_suite = 'nose.collector',
    classifiers = ['Development Status :: 4 - Beta',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python'],
    )
