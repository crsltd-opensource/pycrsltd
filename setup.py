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

try:
    from setuptools import setup, Extension, find_packages
except:#if the user doesn't have setuptools we could install with standard library
    from distutils.core import setup
import pycrsltd#to fetch __version__ etc

setup(name = "pycrsltd",
    packages = ["pycrsltd"],
    include_package_data = True,
    package_data = {}, #DOESN'T AFFECT zip DISTRIBUTION. MUST MODIFY MANIFEST.in TOO
    #metadata
    version = pycrsltd.__version__,
    description = "A Python library to interface with CRS Ltd hardware",
    long_description = open('README.txt').read(),
    author = pycrsltd.__author__,
    author_email = pycrsltd.__author_email__,
    url = pycrsltd.__url__,
    license = pycrsltd.__license__,
    download_url = pycrsltd.__downloadUrl__,
    test_suite = 'nose.collector',
    classifiers = ['Development Status :: 3 - Alpha',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python'],
)

"""
to build:
    sudo python setup.py sdist --format=zip
    sudo python setup.py bdist_egg

to register with PYPI:
    sudo python setup.py register
    python setup.py egg_info
    python setup.py sdist upload
"""