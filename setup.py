#!/usr/bin/python

import os
from setuptools import setup, find_packages

import bitparser

setup(name = 'bitparser',
        version = bitparser.__version__,
        description = 'Binary parsing module',
        long_description=open('README.rst').read(),
        license = bitparser.__license__,
        author = bitparser.__author__,
        author_email = bitparser.__email__,
        url = 'http://projects.oddbit.com/bitparser/',
        packages = [
            'bitparser',
            ],
        )

