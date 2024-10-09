October 9, 2024: Released version 1.2.0:

- Use bundled Noto Sans fonts instead of expecting Verdana to be somewhere on
  the system.
- Test coverage is 100%!
- Add support for Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13.
- Drop support for Python 2.7, 3.5 and 3.6.

April 23, 2019: Released version 1.1.1:

- Drop video mode filtering by aspect ratio (21:9 monitors exist).
- Switch to GitHub for bug tracking.
- Dropped support for Python 3.4.

September 21, 2016: Released version 1.1.0:

- Support Python 3.4 and 3.5 in addition to 2.7.
- Made 'pip install pyspacewar' work.

September 17, 2016: Released version 1.0.0:

- Fixed crash on startup with Numpy >= 1.10.
- Dropped support for Python 2.6.

February 10, 2016: Released version 0.9.8:

- Switched version control system from Bazaar to Git, hosted on GitHub
  (https://github.com/mgedmin/pyspacewar).  The old svn -> bzr conversion
  was incomplete and lacked the oldest revisions; I've reconverted the
  original svn into git this time and stiched the few newest revisions from
  bzr.

March 8, 2010: Released version 0.9.7:

- Don't crash on startup when audio is not available, disable sounds instead.
- Switched version control system from self-hosted Subversion to Bazaar on
  Launchpad (bzr branch lp:pyspacewar).

September 30, 2009: Released version 0.9.6:

- Fixed deprecation warning on Python 2.6.
- Dropped support for Python 2.3.

February 27, 2009: Released version 0.9.5:

- Fixed crash on 64-bit Linux machines.
- Now using https://launchpad.net/ for bug tracking.

June 30, 2008: Released version 0.9.4:

- New icon by Jakub Szypulka, plus all the other goodies from last year.

January 7, 2007: Happy New Year!

- Add sound effects and support for background music (now if I only had some
  music...).
- Show an animation (expanding bubble) when ships respawn.
- Allow up to two keys to be bound to the same action.
- Use 800x600 by default; if your computer is fast enough, you can change to
  a better video mode; if not, give a better first impression by avoiding
  sluggishness.
- Change the options menu: show the current state (e.g. "missile orbits: on")
  instead of the action that would change it ("hide missile orbits").  Add
  an option to toggle sound propagation in vacuum (or, in practical terms,
  whether you hear a sound when a missile hits the computer-controlled ship
  or when it explodes).
- Forgot to actually make a release :(

December 25, 2006: Released version 0.9.3: the Christmas release.

- Keyboard controls can now be customized.
- Keyboard controls and video mode options are stored in a config file.
- Added the -w command line option, in case you desire to override the config
  file.

February 20, 2006: Released version 0.9.2 (also known as the "a month of
procrastination" release).

- Fixed the -f and -d command line options.
- Missiles are now larger and brighter than their orbit trail dots.
- Alt+Enter now also toggles fullscreen mode.
- Make it work in 15 and 16 bit per pixel modes (no aaline).
- Possibly fix the MacOS X "invisible fix" problem I saw (use 2 x aaline
  instead of aalines).
- Added a help screen.
- Added an Options menu.
- Added a New Game menu (the main menu was becoming too cluttered).
- Added a pyspacewar.pyw script for the convenience of Windows users.

January 14, 2006: Released version 0.9.1 with some bug fixes and small
features:

- Use pygame.font.SysFont to locate Verdana.ttf on your system.
- Fix "surfaces must not be locked during blit" bug.
- Fix some cosmetic unit test failures.
- Added a background image.
- Made debug timings HUDs less intrusive.
- Added an ability to specify the desired video mode on the command line.
- The thrusters are now drawn more accurately.

January 8, 2006: After a week of intensive work, I released version 0.9.0.
User-visible changes:

- Added an in-game menu.
- You can drag the viewport around with the mouse (use the right button).
- Automatic zoom in.
- Radars show planet sizes, not just positions.
- Dead ships fade away.
- Information panels have translucent backgrounds.
- Added an icon.

Internal code changes.

- Split the code into several modules in a package.
- Refactored the code extensively, it is now much more flexible.
- Added unit tests.
- Added a distutils setup script.


January 1, 2006: After a very nice New Year's party, I started working on
PySpaceWar again.  I want to refactor the code into separate logic and graphics
parts, and add unit tests.  I want to add a proper in-game menu (start new
game, options, exit, etc.).  In longer term I want to implement a networked
multiplayer mode, and a battle recorder with playback.


November 11, 2005: A minor tweak with zoom level.  It is difficult to implement
things I want with the current code base.  Thinking about a rewrite.


July 1-2, 2005: Minor tweaks, unsuccessful optimisations.


June 29, 2005: Demoed the game during EuroPython 2005 lightning talks session.
Was asked if the game could be played over the network.  Said that no, but
that I accept patches.  Nobody sent me a patch, though.


June 27-29, 2005: EuroPython 2005.  Having much fun with the game.  Sometimes
I'm hacking during the talks.


June 25, 2005: The weekend before EuroPython 2005.  A couple of days ago
my coworker Ignas told me about a game called Gravity Wars.  I found a free
Pascal version on-line and spent a couple of evenings playing it.  I am now
suddenly overcome by a hacking mood.  I will try to write a gravity based
game (Spacewar or Gravity Wars or both) with PyGame.

