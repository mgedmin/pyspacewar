"""
PySpaceWar command line processing and main loop

$Id$
"""

import sys
import optparse

from pyspacewar.ui import GameUI


def use_psyco():
    """Use Psyco (if available) to speed things up."""
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass


def main():
    """Run PySpaceWar."""
    use_psyco()
    ui = GameUI()
    parser = optparse.OptionParser()
    parser.add_option('-f', '--fullscreen', default=False,
                      help='start in full-screen mode',
                      action='store_true', dest='fullscreen')
    parser.add_option('-d', '--debug', default=False,
                      help='show debug timings',
                      action='store_true', dest='debug')
    parser.add_option('-m', '--mode', default=None, metavar='WxH',
                      help='video mode for fullscreen (e.g. -m 640x480);'
                           ' note that in windowed mode the window size be 20%'
                           ' smaller',
                      action='store', dest='mode')
    opts, args = parser.parse_args()
    ui.fullscreen = opts.fullscreen
    ui.show_debug_info = opts.debug
    if opts.mode:
        try:
            w, h = opts.mode.split('x')
            ui.fullscreen_mode = int(w), int(h)
        except ValueError:
            print >> sys.stderr, ('pyspacewar: error: invalid mode: %s'
                                  % opts.mode)
            sys.exit(1)
    ui.init()
    while True:
        ui.wait_for_tick()
        ui.interact()
        ui.draw()

