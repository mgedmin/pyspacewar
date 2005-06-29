PySpace War
===========

Two ships duel in a gravity field.  Gravity doesn't affect the ships
themselves, but it affects the missiles launced by the ships.  You can play
against the computer, or two players can play with one keyboard.

Alternatively you may agree to stay in place and play Gravity Wars by
just launching missiles at a specified angle and speed in turns.

Web page: http://mg.pov.lt/pyspacewar

Requirements:
 * Python (http://www.python.org/)
 * PyGame (http://www.pygame.org/)
 * NumPy (http://numpy.sourceforge.net/)


Player 1 Controls
-----------------

1               - enable/disable computer control
LEFT, RIGHT     - rotate
UP              - accelerate in the direction you're facing
DOWN            - accelerate in the opposite direction
RCTRL           - launch a missile
RALT            - brake (lose 5% speed)
L               - launch a missile (prompt for angle and speed)

Player 2 Controls
-----------------

Player 2 starts in AI-mode.  Press 2 if you want to control it manually.

2               - enable/disable computer control
A, D            - rotate
W               - accelerate in the direction you're facing
S               - accelerate in the opposite direction
LCTRL           - launch a missile
LALT            - brake (lose 5% speed)
C               - launch a missile (prompt for angle and speed)

Other Controls
--------------

Q, ESC          - quit
P               - pause
O               - hide/show missile orbits
F               - toggle full-screen mode
+, -            - zoom in/out

6               - launch 50 missiles to make the game slow to a crawl
                  (for debugging/profiling)


Command Line
------------

-s WxH          - use WxH mode for full-screen mode (e.g. -s 640x480)
                  (windowed mode uses 80% of the specified size)
-f              - start in full-screen mode
-g              - make gravity affect ships too

-o              - use Psyco to perhaps speed things up
-p              - use hotshot to profile the game


Credits
-------

PySpace War was written by Marius Gedminas <marius@pov.lt> during EuroPython
2005 (and a proverbial weekend before that).  Ignas Mikalajūnas <ignas@pov.lt>
contributed the computer AI code.


Licence: GPL (see GPL.txt).

