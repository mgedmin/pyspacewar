PySpaceWar
==========

.. image:: https://github.com/mgedmin/pyspacewar/workflows/build/badge.svg?branch=master
    :target: https://github.com/mgedmin/pyspacewar/actions

Two ships duel in a gravity field.   Gravity doesn't affect the ships
themselves (which have spanking new anti-gravity devices), but it affects
missiles launced by the ships.

You can play against the computer, or two players can play with one keyboard.
There is also a Gravity Wars mode, where the two ships do not move, and the
players repeatedly specify the direction and velocity of their missiles.

Web page: https://mg.pov.lt/pyspacewar

Bug tracker: https://github.com/mgedmin/pyspacewar/issues

Requirements:

* Python (https://www.python.org/), at least version 3.7
* PyGame (https://www.pygame.org/)


Quick start
-----------

Just run 'pyspacewar' and play.  There is no need to build or install anything
(although if you wish to do so, you can use the traditional 'python setup.py
install').


Player 1 Controls
-----------------

LEFT, RIGHT     - rotate
UP              - accelerate in the direction you're facing
DOWN            - accelerate in the opposite direction
RCTRL           - launch a missile
RALT            - brake (lose 5% speed)
1               - enable/disable computer control


Player 2 Controls
-----------------

A, D            - rotate
W               - accelerate in the direction you're facing
S               - accelerate in the opposite direction
LCTRL           - launch a missile
LALT            - brake (lose 5% speed)
2               - enable/disable computer control


Other Controls
--------------

F1              - help
ESC             - escape to menu (pauses current game)
PAUSE           - pause the game
O               - hide/show missile orbits
F, ALT+ENTER    - toggle full-screen mode
+, -            - zoom in/out
mouse wheel     - zoom in/out
left click      - escape to menu (pauses current game)
right drag      - drag the viewport around



Command Line
------------

-f              - start in full-screen mode
-m WxH          - choose video mode for full-screen (e.g. -m 800x600)
-d              - show detailed timings for debugging/optimization


Credits
-------

PySpaceWar was written by Marius Gedminas <marius@pov.lt>.  It is released
under the GNU General Public Licence (see the file named LICENSE).

Ignas Mikalajūnas <ignas@pov.lt> contributed the computer AI code.

The planet images were borrowed from IGE - Outer Space, an open-source on-line
strategy game (https://www.ospace.net/).

The background image is a darkened version of a public domain Hubble Space
Telescope picture of the NGC 3949 galaxy, downloaded from
http://hubblesite.org/newscenter/newsdesk/archive/releases/2004/25/

Icons were contributed by Jakub Szypulka and licenced under the Creative
Commons Share-Alike 3.0 licence.  See
https://cubestuff.wordpress.com/2007/12/23/pyspacewar-goes-tango

