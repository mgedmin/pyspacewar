#!/usr/bin/env python
import ast
import pathlib
import re

from setuptools import setup


here = pathlib.Path(__file__).parent


news = here.joinpath('NEWS.rst').read_text()


long_description = """
Two ships duel in a gravity field.   Gravity doesn't affect
the ships themselves (which have spanking new anti-gravity
devices), but it affects missiles launced by the ships.

You can play against the computer, or two players can play
with one keyboard.  There is also a Gravity Wars mode, where
the two ships do not move, and the players repeatedly
specify the direction and velocity of their missiles.

Latest changes
--------------

""".lstrip('\n') + '\n\n'.join(news.split('\n\n')[:2])


def determine_version():
    metadata = {}
    with (here / 'src' / 'pyspacewar' / 'version.py').open() as f:
        rx = re.compile("(__version__|__author__|__url__|__licence__) = (.*)")
        for line in f:
            m = rx.match(line)
            if m:
                metadata[m.group(1)] = ast.literal_eval(m.group(2))
    return metadata["__version__"]


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
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Games/Entertainment :: Arcade',
    ],
    python_requires=">=3.10",
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
