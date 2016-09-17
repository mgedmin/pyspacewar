#!/usr/bin/env python
import os
import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

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

""" + '\n\n'.join(file('NEWS.rst').read().split('\n\n')[:2])

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
    url='http://mg.pov.lt/pyspacewar/',
    description='A game loosely inspired by the original Spacewar',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Games/Entertainment :: Arcade',
    ],
    scripts=['pyspacewar'],
    packages=['pyspacewar'],
    package_dir={'': 'src'},
    package_data={'pyspacewar': ['images/*', 'sounds/*', 'music/*']},
)
