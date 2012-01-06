#!/usr/bin/env python

from setuptools import setup, find_packages


setupconf = dict(
    name = 'contract',
    version = '0.3',
    license = 'BSD',
    url = 'https://github.com/Deepwalker/contract/',
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
