"""
PySpaceWar command line processing and main loop
"""

import optparse
import sys

from pyspacewar.ui import GameUI


def use_psyco():
    """Use Psyco (if available) to speed things up."""
    try:
        import psyco
        psyco.full()  # pragma: nocover
    except ImportError:
        pass


def main(argv=None):
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
    parser.add_option('--sound', default=None,
                      help='enable sound',
                      action='store_true', dest='sound')
    parser.add_option('--no-sound',
                      help='disable sound',
                      action='store_false', dest='sound')
    parser.add_option('--music', default=None,
                      help='enable music',
                      action='store_true', dest='music')
    parser.add_option('--no-music',
                      help='disable music',
                      action='store_false', dest='music')
    parser.add_option('-d', '--debug', default=False,
                      help='show debug timings',
                      action='store_true', dest='debug')
    parser.add_option('-m', '--mode', default=None, metavar='WxH',
                      help='video mode for fullscreen (e.g. -m 640x480);'
                           ' note that in windowed mode the window size be 20%'
                           ' smaller',
                      action='store', dest='mode')
    opts, args = parser.parse_args(argv or sys.argv)
    if opts.fullscreen is not None:
        ui.fullscreen = opts.fullscreen
    if opts.debug is not None:
        ui.show_debug_info = opts.debug
    if opts.sound is not None:
        ui.sound = opts.sound
    if opts.music is not None:
        ui.music = opts.music
    if opts.mode:
        try:
            w, h = opts.mode.split('x')
            ui.fullscreen_mode = int(w), int(h)
        except ValueError:
            sys.exit('pyspacewar: error: invalid mode: %s' % opts.mode)
    ui.init()
    try:
        while True:
            ui.wait_for_tick()
            ui.interact()
            ui.draw()
    except (KeyboardInterrupt, SystemExit):
        ui.save_settings()
