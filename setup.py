#!/usr/bin/env python

from setuptools import setup
import os.path


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

version = [line for line in read('trafaret/__init__.py').split('\n') if '__VERSION__' in line][0]
exec(version)

setupconf = dict(
    name='trafaret',
    version='.'.join(str(ver) for ver in __VERSION__),
    license='BSD',
    url='https://github.com/Deepwalker/trafaret/',
    author='Barbuza, Deepwalker, nimnull',
    author_email='krivushinme@gmail.com',
    description=('Validation and parsing library'),
    long_description=read('README.rst'),
    keywords='validation form forms data schema',

    packages=['trafaret', 'trafaret.contrib'],
    extras_require=dict(
        objectid=['pymongo>=2.4.1'],
        rfc3339=['python-dateutil>=1.5']
    ),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ]
)

if __name__ == '__main__':
    setup(**setupconf)
