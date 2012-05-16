#!/usr/bin/env python

"""Setup file for veezio api"""

from setuptools import setup, find_packages

VERSION = (0, 1, '0dev')

setup(
    name='quivotequoi-frontend',
    version='.'.join([str(x) for x in VERSION]),
    description="QuiVoteQuoi Front End",
    long_description=open('README.rst', 'r').read(),
    author='Steeve Morin, Thomas Meson, Samuel Clara',
    author_email='contact@veez.io',
    url='http://quivotequoi.fr',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['quivotequoi'],
    install_requires=[
        "simplejson >= 2.3.3",
        "flask >= 0.8",
        "requests >= 0.10.6",
    ],
)
