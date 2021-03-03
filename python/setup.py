#!/usr/bin/env python

"""
setup.py file for MoCo python package
"""

from setuptools import setup

setup(name='moco',
      version='7.3.1.dev21',
      author="Doug Johnston",
      author_email="doug@motive.ai",
      url="http://motive.ai",
      description="""Motive Controller""",
      install_requires=['six>=1.0.0', 'cffi>=1.9.0', 'pyzmq==15.3.0'],
      # could consider using the find_packages function in setuptools
      packages=["moco", "moco.util"]
)
