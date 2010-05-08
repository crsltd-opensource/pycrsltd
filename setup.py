#!/usr/bin/env python

from distutils.core import setup
import pyoptical

setup(name='pyoptical',
      version=pyoptical.__version__,
      description='Pure python interface to OptiCAL',
      author='Valentin Haenel',
      author_email='valentin.haenel@gmx.de',
      py_modules=['pyoptical'],
      scripts=['pyoptical']
     )

