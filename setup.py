#!/usr/bin/env python

from setuptools import setup, find_packages


setupconf = dict(
    name = 'trafaret',
    version = '0.3.1',
    license = 'BSD',
    url = 'https://github.com/Deepwalker/trafaret/',
    author = 'Barbuza, Deepwalker',
    author_email = 'krivushinme@gmail.com',
    description = ('Validation and parsing library'),
    long_description = "Place README here",

    packages = find_packages(),

    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        ],
    )

if __name__ == '__main__':
    setup(**setupconf)
