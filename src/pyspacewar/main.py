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
    ui.load_settings()
    parser = optparse.OptionParser()
    parser.add_option('-f', '--fullscreen', default=None,
                      help='start in full-screen mode',
                      action='store_true', dest='fullscreen')
    parser.add_option('-w', '--windowed',
                      help='start in windowed mode',
                      action='store_false', dest='fullscreen')
    parser.add_option('-d', '--debug', default=False,
                      help='show debug timings',
                      action='store_true', dest='debug')
    parser.add_option('-m', '--mode', default=None, metavar='WxH',
                      help='video mode for fullscreen (e.g. -m 640x480);'
                           ' note that in windowed mode the window size be 20%'
                           ' smaller',
                      action='store', dest='mode')
    opts, args = parser.parse_args()
    if opts.fullscreen is not None:
        ui.fullscreen = opts.fullscreen
    if opts.debug is not None:
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
    try:
        while True:
            ui.wait_for_tick()
            ui.interact()
            ui.draw()
    except (KeyboardInterrupt, SystemExit):
        ui.save_settings()

