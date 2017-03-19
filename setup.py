#!/usr/bin/env python

from setuptools import setup
import os.path


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setupconf = dict(
    name='trafaret',
    version='0.8.1',
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
    entry_points=dict(
        trafaret=[
            '.MongoId = trafaret.contrib.object_id:MongoId [objectid]',
            '.DateTime = trafaret.contrib.rfc_3339:DateTime [rfc3339]'
        ]
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
