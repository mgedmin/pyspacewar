PySpaceWar refactoring branch.

Goals:
 - proper separation of model and presentation
 - nice, clean code
 - unit tests
 - movie record/playback feature
 - multiplayer mode

Plan:
 - consider the existing pyspacewar.py as a throw-away prototype
 - start using Test Driven Development, but don't hesitate copy and paste
   code from the prototype once you have tests
 - write just enough model classes for a simple game in world.py
 - write some simple GUI code in ui.py to get the game playable
 - extend model and GUI to get existing features
