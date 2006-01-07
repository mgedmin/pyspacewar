#!/usr/bin/python
"""
A game inspired by Space War.

Copyright (c) 2005-2006 Marius Gedminas and Ignas Mikalajunas

Consider this game GPLed.

$Id$
"""

import sys

from ui import GameUI


def main():
    ui = GameUI()
    if '-f' in sys.argv:
        ui.fullscreen = True
    ui.init()
    while True:
        ui.wait_for_tick()
        ui.interact()
        ui.draw()


if __name__ == '__main__':
    main()
