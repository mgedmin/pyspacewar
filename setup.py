#!/usr/bin/env python
import os
import glob
from distutils.core import setup

long_description = """\
A game loosely inspired by the original Spacewar.

Two ships duel in a gravity field.   Gravity doesn't affect
the ships themselves (which have spanking new anti-gravity
devices), but it affects missiles launced by the ships.

You can play against the computer, or two players can play
with one keyboard.  There is also a Gravity Wars mode, where
the two ships do not move, and the players repeatedly
specify the direction and velocity of their missiles.
"""

planet_images = glob.glob(os.path.join('images', 'planet*.png'))

setup(name='pyspacewar',
      version='0.9.0',
      author='Marius Gedminas',
      author_email='marius@pov.lt',
      license='GPL',
      platforms=['any'],
      url='http://mg.pov.lt/pyspacewar/',
      description='A game loosely inspired by the original Spacewar',
      long_description=long_description,
      classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: MacOS X',
            'Environment :: Win32 (MS Windows)',
            'Environment:: X11 Applications',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Games/Entertainment :: Arcade',
        ],
      scripts=['pyspacewar'],
      py_modules=['ui', 'game', 'world', 'ai'],
      data_files=[('images', ['images/pyspacewar-32x32.png',
                              'images/title.png'] + planet_images),
                 ],
     )
