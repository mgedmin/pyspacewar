Features that block the 1.0 release:

- invisible ships on Mac OS X (I think this is fixed now)

Features that would be nice for 1.0, but that I could live without:

- some sort of warp-in effect when the ships respawn
- frag limit: once reached, a player becomes victorious and both players
  are warped to a new planet system
- optimize: I'd like it to work reasonably well on 600 MHz machines
- customizable video features (turn off alpha blending of HUD items or the
  background image, to speed things up, etc.)

Smaller wishlist items:

- when the game is paused, don't keep redrawing the same things every frame
  (especially in the help screen)
- say 'Paused' somewhere when you press the Pause key (though I want it not to
  interfere with screenshots; maybe put it in the title bar if not
  in fullscreen mode?)
- preserve aspect ratio for the background image (scale & crop)
- three modes for debug panels, cycled with F12: no debug; show fps/#objects,
  show fps/#objects + detailed timings
- automatically pause the game when you lose window focus
- use pygame.time.get_ticks() instead of time.time() for timings

Larger wishlist items:

- some music/sound effects
- nice sprites for the ships (I have code in a branch that draws sprites, but
  my drawings are ugly)
- customizable key bindings
- game recording/playback (this can be a prototype for multiplayer)
- multiplayer mode

Planned refactorings and cleanups:

- use Rects to simplify a lot of layout code
- keep track of dirty rectangles; pygame.display.flip() may take more than
  50 ms on some machines
- split ui.py into smaller modules (spin off hud.py, viewport.py)
- unit tests for ai.py
- refactor ai.py
- move Vector into a new module vector.py
- adjust other constants so that I could set Game.DELTA_TIME == 1.0
- get rid of Game.DELTA_TIME and the dt argument to World.update

Hints for optimization:

- what are those 10 ms spent on "other" outside update/draw/wait?
- what exactly takes 6 ms to draw outside page flipping and missile trails?
- when the game is too slow and starts dropping frames, debug timing
  shows that it still spends 7 to 30 ms idling.  Why?
