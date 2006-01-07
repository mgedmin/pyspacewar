#!/usr/bin/python
"""
A game inspired by Space War.

Copyright (c) 2005-2006 Marius Gedminas and Ignas Mikalajunas.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

$Id$
"""

import sys

from ui import GameUI


def main():
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    ui = GameUI()
    if '-f' in sys.argv:
        ui.fullscreen = True
    if '-d' in sys.argv:
        ui.show_debug_info = True
    ui.init()
    while True:
        ui.wait_for_tick()
        ui.interact()
        ui.draw()


if __name__ == '__main__':
    main()
