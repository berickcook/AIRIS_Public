import pygame
from constants import REP_MAP_START, REP_POS_SIZE


class GameObjectColor(object):

    def __init__(self, identification_number, color):
        # Store id and position pixel size
        self.id = identification_number

        # Color square
        self.rep = pygame.Surface(REP_POS_SIZE)
        self.rep.fill(pygame.Color(color))

    def draw_game_image(self, view, x, y, direction=0):
        pass

    def draw_representation_image(self, view, x, y):
        # map_start is the pixel coordinates of where the game map starts
        # x and y are the position coordinates of this Floor object

        # draw representation image
        view.surface.blit(self.rep, (REP_MAP_START[0] + x * REP_POS_SIZE[0],
                                     REP_MAP_START[1] + y * REP_POS_SIZE[1]))
        pygame.display.flip()


class BumpSprite(GameObjectColor):
    def __init__(self):
        super(BumpSprite, self).__init__(19.0, "#FF0000")


class FeelEmptySprite(GameObjectColor):
    def __init__(self):
        super(FeelEmptySprite, self).__init__(19.0, "#c0c0c0")


class FeelWallSprite(GameObjectColor):
    def __init__(self):
        super(FeelWallSprite, self).__init__(19.0, "#000000")
