import pygame
from pygame.locals import *
import time
from constants import *


class GameObject(object):

    def __init__(self, identification_number, image_file_path, represent_file_path):

        # store id and position pixel size
        self.id = identification_number

        # get floor image
        im0 = pygame.image.load('./images/Puzzle_Game/Game/Floor_0.png')
        colorkey = im0.get_at((0,0))
        im0.set_colorkey(colorkey, RLEACCEL)
        self.floor_image = pygame.transform.scale(im0, GAME_POS_SIZE)

        # get main image
        self.game_image_file_path = image_file_path
        im1 = pygame.image.load(self.game_image_file_path)
        self.image1 = pygame.transform.scale(im1, GAME_POS_SIZE)

        # get representation image
        self.representation_image_file_path = represent_file_path
        rep = pygame.image.load(self.representation_image_file_path)
        self.rep = pygame.transform.scale(rep, REP_POS_SIZE)

    def draw_game_image(self, view, x, y):
        # map_start is the pixel coordnates of where the game map starts
        # x and y are the position coordinates of this Floor object

        # draw floor first every time
        view.surface.blit(self.floor_image, \
            (GAME_MAP_START[0]+x*GAME_POS_SIZE[0], \
                GAME_MAP_START[1]+y*GAME_POS_SIZE[1]))

        # then draw other object over top
        view.surface.blit(self.image1, \
            (GAME_MAP_START[0]+x*GAME_POS_SIZE[0], \
                GAME_MAP_START[1]+y*GAME_POS_SIZE[1]))

        pygame.display.flip()

    def draw_representation_image(self, view, x, y):
        # map_start is the pixel coordnates of where the game map starts
        # x and y are the position coordinates of this Floor object

        # draw representation image
        view.surface.blit(self.rep, \
            (REP_MAP_START[0]+x*REP_POS_SIZE[0], \
                REP_MAP_START[1]+y*REP_POS_SIZE[1]))

        pygame.display.flip()


''' Types of Objects:

    ----------------------------------------------------
    id   Object
    ----------------------------------------------------
    0    floor
    1    character
    2    wall
    3    battery
    4    door
    5    key
    6    fire extinguisher
    7    fire
    8    1 way arrow right
    9    1 way arrow left
    10   1 way arrow down
    11   1 way arrow up
    12   open door
    13   player character standing on top of right arrow
    14   player character standing on top of left arrow
    15   player character standing on top of down arrow
    16   player character standing on top of up arrow
    17   player character standing in open door
    ----------------------------------------------------

    Figured out how to display images overlayed on top of
    each other from this source:
        https://github.com/codingchili/py-race/blob/master/loader.py

    '''


class Character(GameObject):

    def __init__(self):

        super(Character, self).__init__(1.0, \
            './images/Puzzle_Game/Game/CharS_0.png', \
            './images/Puzzle_Game/Represent/Represent_1.png')

class Floor(GameObject):

    def __init__(self):

        super(Floor, self).__init__(0.0, \
            './images/Puzzle_Game/Game/Floor_0.png', \
            './images/Puzzle_Game/Represent/Represent_0.png')
class Wall(GameObject):

    def __init__(self):

        super(Wall, self).__init__(2.0, \
            './images/Puzzle_Game/Game/WallS_0.png', \
            './images/Puzzle_Game/Represent/Represent_2.png')

class Fire(GameObject):

    def __init__(self):

        super(Fire, self).__init__(7.0, \
            './images/Puzzle_Game/Game/FireS_0.png', \
            './images/Puzzle_Game/Represent/Represent_7.png')
class Extinguisher(GameObject):

    def __init__(self):

        super(Extinguisher, self).__init__(6.0, \
            './images/Puzzle_Game/Game/ExtinguishS_0.png', \
            './images/Puzzle_Game/Represent/Represent_6.png')

class Battery(GameObject):

    def __init__(self):

        super(Battery, self).__init__(3.0, \
            './images/Puzzle_Game/Game/BatteryS_0.png', \
            './images/Puzzle_Game/Represent/Represent_3.png')

class Key(GameObject):

    def __init__(self):

        super(Key, self).__init__(5.0, \
            './images/Puzzle_Game/Game/KeyS_0.png', \
            './images/Puzzle_Game/Represent/Represent_5.png')
class Door(GameObject):

    def __init__(self):

        super(Door, self).__init__(4.0, \
            './images/Puzzle_Game/Game/DoorS_0.png', \
            './images/Puzzle_Game/Represent/Represent_4.png')
class OpenDoor(GameObject):

    def __init__(self):

        super(OpenDoor, self).__init__(12.0, \
            './images/Puzzle_Game/Game/DoorOpenS_0.png', \
            './images/Puzzle_Game/Represent/Represent_12.png')

class RightArrow(GameObject):

    def __init__(self):

        super(RightArrow, self).__init__(8.0, \
            './images/Puzzle_Game/Game/ArrowRS_0.png', \
            './images/Puzzle_Game/Represent/Represent_8.png')
class LeftArrow(GameObject):

    def __init__(self):

        super(LeftArrow, self).__init__(9.0, \
            './images/Puzzle_Game/Game/ArrowLS_0.png', \
            './images/Puzzle_Game/Represent/Represent_9.png')
class DownArrow(GameObject):

    def __init__(self):

        super(DownArrow, self).__init__(10.0, \
            './images/Puzzle_Game/Game/ArrowDS_0.png', \
            './images/Puzzle_Game/Represent/Represent_10.png')
class UpArrow(GameObject):

    def __init__(self):

        super(UpArrow, self).__init__(11.0, \
            './images/Puzzle_Game/Game/ArrowUS_0.png', \
            './images/Puzzle_Game/Represent/Represent_11.png')

class CharacterOnObject(GameObject):

    def __init__(self, identification_number, image_file_path2, represent_file_path):

        super(CharacterOnObject, self).__init__(identification_number, \
            './images/Puzzle_Game/Game/CharS_0.png', represent_file_path)

        self.game_image_file_path2 = image_file_path2
        im2 = pygame.image.load(self.game_image_file_path2)
        colorkey = im2.get_at((0,0))
        im2.set_colorkey(colorkey, RLEACCEL)
        self.image2 = pygame.transform.scale(im2, GAME_POS_SIZE)

    def draw_game_image(self, view, x, y):
        # map_start is the pixel coordnates of where the game map starts
        # x and y are the position coordinates of this Floor object

        # draw floor first
        view.surface.blit(self.floor_image, \
            (GAME_MAP_START[0]+x*GAME_POS_SIZE[0], GAME_MAP_START[1]+y*GAME_POS_SIZE[1]))

        # draw next object (Arrow or OpenDoor)
        view.surface.blit(self.image2, \
            (GAME_MAP_START[0]+x*GAME_POS_SIZE[0], \
             GAME_MAP_START[1]+y*GAME_POS_SIZE[1]))

        # draw character
        view.surface.blit(self.image1, \
            (GAME_MAP_START[0]+x*GAME_POS_SIZE[0], \
             GAME_MAP_START[1]+y*GAME_POS_SIZE[1]))

        pygame.display.flip()
class CharacterOnRightArrow(CharacterOnObject):

    def __init__(self):

        super(CharacterOnRightArrow, self).__init__(13.0, \
            './images/Puzzle_Game/Game/ArrowRS_0.png', \
            './images/Puzzle_Game/Represent/Represent_13.png')
class CharacterOnLeftArrow(CharacterOnObject):

    def __init__(self):

        super(CharacterOnLeftArrow, self).__init__(14.0, \
            './images/Puzzle_Game/Game/ArrowLS_0.png', \
            './images/Puzzle_Game/Represent/Represent_14.png')
class CharacterOnDownArrow(CharacterOnObject):

    def __init__(self):

        super(CharacterOnDownArrow, self).__init__(15.0, \
        './images/Puzzle_Game/Game/ArrowDS_0.png', \
        './images/Puzzle_Game/Represent/Represent_15.png')
class CharacterOnUpArrow(CharacterOnObject):

    def __init__(self):

        super(CharacterOnUpArrow, self).__init__(16.0, \
            './images/Puzzle_Game/Game/ArrowUS_0.png', \
            './images/Puzzle_Game/Represent/Represent_16.png')
class CharacterOnOpenDoor(CharacterOnObject):

    def __init__(self):

        super(CharacterOnOpenDoor, self).__init__(17.0, \
            './images/Puzzle_Game/Game/DoorOpenS_0.png', \
            './images/Puzzle_Game/Represent/Represent_16.png')
