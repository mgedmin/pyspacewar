#!/usr/bin/env python
import os
import sys

from setuptools import setup


with open('NEWS.rst') as f:
    news = f.read()

long_description = """\
Two ships duel in a gravity field.   Gravity doesn't affect
the ships themselves (which have spanking new anti-gravity
devices), but it affects missiles launced by the ships.

You can play against the computer, or two players can play
with one keyboard.  There is also a Gravity Wars mode, where
the two ships do not move, and the players repeatedly
specify the direction and velocity of their missiles.

Latest changes
--------------

""" + '\n\n'.join(news.split('\n\n')[:2])

pkgdir = os.path.join('src', 'pyspacewar')


def determine_version():
    sys.path.insert(0, 'src')
    from pyspacewar.version import version
    del sys.path[0]
    return version


version = determine_version()

setup(
    name='pyspacewar',
    version=version,
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    license='GPL',
    platforms=['any'],
    url='https://mg.pov.lt/pyspacewar/',
    description='A game loosely inspired by the original Spacewar',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Games/Entertainment :: Arcade',
    ],
    python_requires=">=3.7",
    scripts=['pyspacewar'],
    packages=['pyspacewar'],
    package_dir={'': 'src'},
    package_data={
        'pyspacewar': [
            'icons/*',
            'images/*',
            'music/*',
            'sounds/*',
            'fonts/*',
        ],
    },
    install_requires=['pygame'],
    extras_require={
        'numpy': [
            'numpy',
        ],
        'test': [
            'mock',
            'pytest',
        ],
    },
)
