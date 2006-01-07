PySpaceWar
==========

Two ships duel in a gravity field.   Gravity doesn't affect the ships
themselves (which have spanking new anti-gravity devices), but it affects
missiles launced by the ships.

You can play against the computer, or two players can play with one keyboard.
There is also a Gravity Wars mode, where the two ships do not move, and the
players repeatedly specify the direction and velocity of their missiles.

Web page: http://mg.pov.lt/pyspacewar

Requirements:
 * Python (http://www.python.org/), at least version 2.3
 * PyGame (http://www.pygame.org/)


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

ESC             - escape to menu (pauses current game)
O               - hide/show missile orbits
F               - toggle full-screen mode
+, -            - zoom in/out
mouse wheel     - zoom in/out
left click      - escape to menu (pauses current game)
right drag      - drag the viewport around


Command Line
------------

-f              - start in full-screen mode


Credits
-------

PySpaceWar was written by Marius Gedminas <marius@pov.lt> during EuroPython
2005 (and a proverbial weekend before that).  Ignas Mikalajūnas <ignas@pov.lt>
contributed the computer AI code.


Licence: GPL (see GPL.txt).
