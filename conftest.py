import os

import pytest
import pygame


@pytest.fixture(scope='session', autouse=True)
def setUp(test=None):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.init()  # so that pygame.key.name() works
