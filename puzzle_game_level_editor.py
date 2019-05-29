import pygame
import time, sys, csv, copy, os
from pygame.locals import QUIT, KEYDOWN
from editor_objects import *
from editor_constants import *
from other_useful_functions import pprint


class PyGameView(object):
    '''
        PyGameView controls the display
    '''

    def __init__(self, model):

        self.model = model
        self.screen = pygame.display.set_mode(GAME_SCREEN_SIZE) # a pygame screen
        self.surface = pygame.Surface(GAME_SCREEN_SIZE) # a pygame surface is the thing you draw on

        self.show_view = True # toggle display
        self.show_controls = False # toggle control display

        self.obj_select = 0
        self.lvl_val = model.wall

        self.sprites = []
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/WallS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/DoorS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/KeyS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/FireS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/ExtinguishS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/ArrowUS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/ArrowDS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/ArrowLS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/ArrowRS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/BatteryS_0.png'))
        self.sprites.append(pygame.image.load('./images/Puzzle_Game/Game/CharS_0.png'))

    def draw(self):

        # commented out because we're only updating squares if they change
        # # fill background
        # self.surface.fill(pygame.Color('black'))

        pygame.draw.rect(self.surface, 4210752, pygame.Rect(0, 0, 640, 64))
        pygame.draw.rect(self.surface, 4210752, pygame.Rect(0, 544, 640, 64))

        pygame.draw.rect(self.surface, 8421504, pygame.Rect(2, 2, 636, 60))
        pygame.draw.rect(self.surface, 8421504, pygame.Rect(2, 546, 636, 60))

        pygame.draw.rect(self.surface, 12632256, pygame.Rect(4, 4, 632, 56))
        pygame.draw.rect(self.surface, 12632256, pygame.Rect(4, 548, 632, 56))

        if controller.paused:
            for i in range(11):
                if self.obj_select == i:
                    pygame.draw.rect(self.surface, 16777215, pygame.Rect(8+(48*i), 8, 48, 48))
                else:
                    pygame.draw.rect(self.surface, 8421504, pygame.Rect(8+(48*i), 8, 48, 48))

                pygame.draw.rect(self.surface, 0, pygame.Rect(8+(48*i),8,48,48), 1)
                self.surface.blit(self.sprites[i], ((16*(i+1))+(32*i), 16))

            if model.character_start_pos == (-1, -1) or model.num_batteries == 0:
                pygame.draw.rect(self.surface, 4210752, pygame.Rect(544, 16, 84, 32))
                pygame.draw.rect(self.surface, 8421504, pygame.Rect(546, 18, 80, 28))
                if model.num_batteries == 0:
                    self.draw_text("NO BATTS", 548, 25, 23)
                elif model.character_start_pos == (-1, -1):
                    self.draw_text("NO BOT", 556, 25, 23)
            else:
                if not controller.verified:
                    pygame.draw.rect(self.surface, 32768, pygame.Rect(544, 16, 84, 32))
                    pygame.draw.rect(self.surface, 65280, pygame.Rect(546, 18, 80, 28))
                    self.draw_text("PLAY", 567, 25, 23)
                else:
                    pygame.draw.rect(self.surface, 32768, pygame.Rect(544, 16, 84, 32))
                    self.draw_text("SOLVED", 557, 25, 23)

            pygame.draw.rect(self.surface, pygame.Color(128, 0, 0, 255), pygame.Rect(8, 560, 84, 32))
            pygame.draw.rect(self.surface, pygame.Color(255, 0, 0, 255), pygame.Rect(10, 562, 80, 28))
            self.draw_text("CLEAR", 23, 569, 23)

            if controller.verified:
                pygame.draw.rect(self.surface, 32768, pygame.Rect(544, 560, 84, 32))
                pygame.draw.rect(self.surface, 65280, pygame.Rect(546, 562, 80, 28))
                self.draw_text("SAVE", 567, 569, 23)
            else:
                pygame.draw.rect(self.surface, 4210752, pygame.Rect(544, 560, 84, 32))
                pygame.draw.rect(self.surface, 8421504, pygame.Rect(546, 562, 80, 28))
                self.draw_text("SOLVE", 562, 569, 23)

            if controller.saved:
                pygame.draw.rect(self.surface, 32768, pygame.Rect(544, 560, 84, 32))
                self.draw_text("SAVED", 562, 569, 23)

        self.draw_game_map()

        # update display
        pygame.display.update()

    def draw_game_map(self):

        # variable setup
        w, h = GAME_MAP_GRID # number of positions wide and high
        ms = GAME_MAP_START

        # draw each position in the grid
        for x in range(w):
            for y in range(h):
                if self.model.change_in_game_map[x][y]:
                   self.model.game_map[x][y].draw_game_image(self, x, y)

    def draw_text(self, text, x, y, size, color = (0, 0, 0)):
        basicfont = pygame.font.SysFont(None, size)
        text_render = basicfont.render(
            text, False, color)
        self.surface.blit(text_render, (x, y))


class Model(object):
    '''
        Model represents the state of all entities in
        the environment and drawing parameters

    '''

    # this function initializes the model
    def __init__(self, controller):
        '''
            initialize model, environment, and default keyboard controller states
        Args:
            width (int): width of window in pixels
            height (int): height of window in pixels
        '''

        # game setup parameters
        self.show = True # show current model
        self.controller = controller

        # maze game setup
        self.make_singletons()
        self.current_maze = 0
        self.get_next_maze()
        self.set_change_in_game_map(True)

    # this function updates the model
    def update(self):

        self.set_change_in_game_map(False)

        # get user input
        player_action = self.get_action()

        # update the game according to the player's input
        self.game_logic(player_action)

        # go to next level if player beats the current level
        if self.batteries_collected == self.num_batteries or self.maze_reset:
            if self.batteries_collected == self.num_batteries:
                controller.paused = True
                controller.verified = True
            for x in range(len(controller.game_map)):
                for y in range(len(controller.game_map[x])):
                    self.game_map[x][y] = controller.game_map[x][y]
            self.character_current_pos = copy.deepcopy(controller.character_start_pos)
            self.character_start_pos = copy.deepcopy(controller.character_start_pos)
            self.num_batteries = copy.deepcopy(controller.num_batteries)
            self.character_current_floor = self.floor
            self.batteries_collected = 0
            self.extinguishers_collected = 0
            self.keys_collected = 0
            self.set_change_in_game_map(True)
            controller.is_there_input = True

    def get_action(self):
        return self.controller.player_input

    # these functions controls game logic
    def game_logic(self, player_input):

        if player_input != 'nothing':
            if player_input == 'up':
                character_new_pos = (self.character_current_pos[0], self.character_current_pos[1] - 1)
            if player_input == 'down':
                character_new_pos = (self.character_current_pos[0], self.character_current_pos[1] + 1)
            if player_input == 'left':
                character_new_pos = (self.character_current_pos[0] - 1, self.character_current_pos[1])
            if player_input == 'right':
                character_new_pos = (self.character_current_pos[0] + 1, self.character_current_pos[1])

            new_tile = self.game_map[character_new_pos[0]][character_new_pos[1]]
            if isinstance(new_tile, Floor):
                self.move_character(new_tile, character_new_pos, self.character)

            elif isinstance(new_tile, Wall):
                pass

            elif isinstance(new_tile, Battery):
                self.move_character(new_tile, character_new_pos, self.character)
                self.collect_battery(character_new_pos)

            elif isinstance(new_tile, RightArrow):
                if player_input != 'left':
                    self.move_character(new_tile, character_new_pos, self.character_on_right_arrow)

            elif isinstance(new_tile, LeftArrow):
                if player_input != 'right':
                    self.move_character(new_tile, character_new_pos, self.character_on_left_arrow)

            elif isinstance(new_tile, UpArrow):
                if player_input != 'down':
                    self.move_character(new_tile, character_new_pos, self.character_on_up_arrow)

            elif isinstance(new_tile, DownArrow):
                if player_input != 'up':
                    self.move_character(new_tile, character_new_pos, self.character_on_down_arrow)

            elif isinstance(new_tile, Fire):
                if self.extinguishers_collected == 0:
                    self.reset_maze()
                else:
                    self.move_character(new_tile, character_new_pos, self.character)
                    self.character_current_floor = self.floor
                    self.extinguishers_collected -= 1

            elif isinstance(new_tile, Extinguisher):
                self.move_character(new_tile, character_new_pos, self.character)
                self.collect_extinguisher(character_new_pos)

            elif isinstance(new_tile, Door):
                if self.keys_collected == 0:
                    pass
                else:
                    self.move_character(new_tile, character_new_pos, self.character_on_open_door)
                    self.keys_collected -= 1

            elif isinstance(new_tile, OpenDoor):
                self.move_character(new_tile, character_new_pos, self.character_on_open_door)

            elif isinstance(new_tile, Key):
                self.move_character(new_tile, character_new_pos, self.character)
                self.collect_key(character_new_pos)

    def move_character(self, new_tile, character_new_pos, character_and_floor):

        character_old_floor = self.character_current_floor
        character_old_pos = self.character_current_pos

        if character_and_floor != self.character_on_open_door:
            self.character_current_floor = new_tile
        else:
            self.character_current_floor = self.open_door
        self.character_current_pos = character_new_pos

        self.game_map[self.character_current_pos[0]][self.character_current_pos[1]] = character_and_floor

        self.change_in_game_map[self.character_current_pos[0]][self.character_current_pos[1]] = True

        self.game_map\
        [character_old_pos[0]][character_old_pos[1]] = character_old_floor

        self.change_in_game_map[character_old_pos[0]][character_old_pos[1]] = True

    def collect_battery(self, character_new_pos):
        self.batteries_collected += 1
        self.character_current_floor = self.floor

    def collect_extinguisher(self, character_new_pos):
        self.extinguishers_collected += 1
        self.character_current_floor = self.floor

    def collect_key(self, character_new_pos):
        self.keys_collected += 1
        self.character_current_floor = self.floor

    def reset_maze(self):
        self.current_maze -= 1
        self.maze_reset = True
        # self.update()

    # these functions initialize the maze levels
    def load_maze(self):

        game_map = self.floor_init()
        with open('custom_levels/' + str(sys.argv[1]), 'r') as File:
            read = csv.reader(File, delimiter=',')
            for r, row in enumerate(read):
                row[0] = int(row[0])
                row[1] = int(row[1])
                row[2] = int(row[2])

                if r == 0:
                    self.character_start_pos = (row[0], row[1])
                    self.character_current_pos = (row[0], row[1])
                    self.character_current_floor = self.floor
                    self.num_batteries = row[2]
                else:
                    if row[2] == 1:
                        game_map[row[0]][row[1]] = self.character
                    if row[2] == 2:
                        game_map[row[0]][row[1]] = self.wall
                    if row[2] == 3:
                        game_map[row[0]][row[1]] = self.battery
                    if row[2] == 4:
                        game_map[row[0]][row[1]] = self.door
                    if row[2] == 5:
                        game_map[row[0]][row[1]] = self.key
                    if row[2] == 6:
                        game_map[row[0]][row[1]] = self.extinguisher
                    if row[2] == 7:
                        game_map[row[0]][row[1]] = self.fire
                    if row[2] == 8:
                        game_map[row[0]][row[1]] = self.right_arrow
                    if row[2] == 9:
                        game_map[row[0]][row[1]] = self.left_arrow
                    if row[2] == 10:
                        game_map[row[0]][row[1]] = self.down_arrow
                    if row[2] == 11:
                        game_map[row[0]][row[1]] = self.up_arrow

        pygame.display.set_caption('Puzzle Game Level Editor - Editing '+str(sys.argv[1]))
        self.game_map = game_map

    def get_next_maze(self):

        self.set_change_in_game_map(True)

        self.current_maze += 1

        try:
            self.load_maze()

        except FileNotFoundError:
            self.current_maze = 1
            try:
                self.load_maze()
            except FileNotFoundError:
                print('ERROR: No levels to load!')
                print('Use the included level editor to create levels and place them in /custom_levels')
                print('They must be named 1.csv, 2.csv, 3.csv, ...')
                interrupt = input()
                raise Exception

        except IndexError:
            self.game_map = self.floor_init()
            self.num_batteries = 0
            self.character_start_pos = (-1, -1)
            self.character_current_pos = (-1, -1)
            self.character_current_floor = self.floor
            self.get_name = str(len(os.listdir(os.getcwd()+'/custom_levels'))+1) + '.csv'
            pygame.display.set_caption('Puzzle Game Level Editor - Creating new level: ' + self.get_name)

        self.batteries_collected = 0
        self.extinguishers_collected = 0
        self.keys_collected = 0
        self.maze_reset = False

    # these are helper functions for making maze levels
    def floor_init(self):
        # initialize everything to a floor tile
        game_map = []
        for x in range(GAME_MAP_GRID[0]):
            game_map.append([])
            for y in range(GAME_MAP_GRID[1]):
                game_map[x].append(self.floor)
        return game_map

    def make_singletons(self):

        self.character    = Character()
        self.floor        = Floor()
        self.wall         = Wall()
        self.fire         = Fire()
        self.extinguisher = Extinguisher()
        self.battery = Battery()
        self.key     = Key()
        self.door    = Door()
        self.open_door   = OpenDoor()
        self.right_arrow = RightArrow()
        self.left_arrow  = LeftArrow()
        self.down_arrow  = DownArrow()
        self.up_arrow    = UpArrow()
        self.character_on_right_arrow = CharacterOnRightArrow()
        self.character_on_left_arrow  = CharacterOnLeftArrow()
        self.character_on_down_arrow  = CharacterOnDownArrow()
        self.character_on_up_arrow    = CharacterOnUpArrow()
        self.character_on_open_door   = CharacterOnOpenDoor()

    # this function is used to render the game faster
    # by only rendering the parts of the game that
    # changed from the previous time step
    def set_change_in_game_map(self, state):
        self.change_in_game_map = []
        for x in range(GAME_MAP_GRID[0]):
            self.change_in_game_map.append([])
            for y in range(GAME_MAP_GRID[1]):
                self.change_in_game_map[x].append(state)


class PyGameKeyboardController(object):
    '''
        Keyboard controller that responds to keyboard input
    '''

    def __init__(self):

        self.paused = True
        self.player_input = 'nothing'
        self.mb_left = False
        self.mb_right = False
        self.first = True
        self.num_batteries = 0
        self.character_start_pos = (-1, -1)
        self.is_there_input = False
        self.verified = False
        self.saved = False
        self.save_map = []
        self.save_val = 2

    def handle_input(self):

        self.is_there_input = False

        if self.first:
            self.game_map = self.floor_init()
            self.character_start_pos = model.character_start_pos
            self.num_batteries = model.num_batteries
            for x in range(len(self.game_map)):
                self.save_map.append([])
                for y in range(len(self.game_map[x])):
                    self.game_map[x][y] = model.game_map[x][y]
                    self.save_map[x].append(0)
                    if self.game_map[x][y] == model.wall:
                        self.save_map[x][y] = 2
                    if self.game_map[x][y] == model.door:
                        self.save_map[x][y] = 4
                    if self.game_map[x][y] == model.key:
                        self.save_map[x][y] = 5
                    if self.game_map[x][y] == model.fire:
                        self.save_map[x][y] = 7
                    if self.game_map[x][y] == model.extinguisher:
                        self.save_map[x][y] = 6
                    if self.game_map[x][y] == model.up_arrow:
                        self.save_map[x][y] = 11
                    if self.game_map[x][y] == model.down_arrow:
                        self.save_map[x][y] = 10
                    if self.game_map[x][y] == model.left_arrow:
                        self.save_map[x][y] = 9
                    if self.game_map[x][y] == model.right_arrow:
                        self.save_map[x][y] = 8
                    if self.game_map[x][y] == model.battery:
                        self.save_map[x][y] = 3
                    if self.game_map[x][y] == model.character:
                        self.save_map[x][y] = 1
            self.first = False

        for event in pygame.event.get():
            if event.type == QUIT:
                return False, self.is_there_input
            else:
                if event.type != KEYDOWN:
                    if event.type == pygame.MOUSEBUTTONDOWN:

                        if self.paused:
                            if event.button == 1:
                                self.mb_left = True
                            elif event.button == 3:
                                self.mb_right = True

                    if event.type == pygame.MOUSEBUTTONUP:

                        if event.button == 1:
                            self.mb_left = False
                        elif event.button == 3:
                            self.mb_right = False

                elif event.key == pygame.K_SPACE:
                    if self.character_start_pos != (-1, -1) and self.num_batteries > 0:
                        if not self.paused:
                            for x in range(len(self.game_map)):
                                for y in range(len(self.game_map[x])):
                                    model.game_map[x][y] = self.game_map[x][y]
                            model.character_current_pos = copy.deepcopy(self.character_start_pos)
                            model.character_start_pos = copy.deepcopy(self.character_start_pos)
                            model.num_batteries = copy.deepcopy(self.num_batteries)
                            model.character_current_floor = model.floor
                            model.batteries_collected = 0
                            model.extinguishers_collected = 0
                            model.keys_collected = 0
                            model.set_change_in_game_map(True)
                        self.paused = not self.paused
                        self.is_there_input = True
                elif event.key == pygame.K_k:
                    view.show_controls = not view.show_controls
                elif event.key == pygame.K_v:
                    view.show_view = not view.show_view

        mouse_pos = pygame.mouse.get_pos()
        if self.mb_left:
            if 8 <= mouse_pos[0] <= 528 and 8 <= mouse_pos[1] <= 56:
                view.obj_select = (mouse_pos[0] - 8) // 48

                if view.obj_select == 0:
                    view.lvl_val = model.wall
                    self.save_val = 2
                if view.obj_select == 1:
                    view.lvl_val = model.door
                    self.save_val = 4
                if view.obj_select == 2:
                    view.lvl_val = model.key
                    self.save_val = 5
                if view.obj_select == 3:
                    view.lvl_val = model.fire
                    self.save_val = 7
                if view.obj_select == 4:
                    view.lvl_val = model.extinguisher
                    self.save_val = 6
                if view.obj_select == 5:
                    view.lvl_val = model.up_arrow
                    self.save_val = 11
                if view.obj_select == 6:
                    view.lvl_val = model.down_arrow
                    self.save_val = 10
                if view.obj_select == 7:
                    view.lvl_val = model.left_arrow
                    self.save_val = 9
                if view.obj_select == 8:
                    view.lvl_val = model.right_arrow
                    self.save_val = 8
                if view.obj_select == 9:
                    view.lvl_val = model.battery
                    self.save_val = 3
                if view.obj_select == 10:
                    view.lvl_val = model.character
                    self.save_val = 1

            if 64 < mouse_pos[1] < 544:
                self.saved = False
                self.verified = False
                if view.obj_select == 9 and model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] != model.battery:
                    self.num_batteries += 1
                    model.num_batteries += 1
                if view.obj_select == 10:
                    if model.character_start_pos != (-1, -1) and (model.character_current_pos[0] != mouse_pos[0] // 32 or model.character_current_pos[1] != (mouse_pos[1] - 64) // 32):
                        self.game_map[model.character_current_pos[0]][model.character_current_pos[1]] = model.floor
                        self.save_map[model.character_current_pos[0]][model.character_current_pos[1]] = 0
                        model.game_map[model.character_current_pos[0]][model.character_current_pos[1]] = model.floor
                        model.change_in_game_map[model.character_current_pos[0]][model.character_current_pos[1]] = True
                    self.character_start_pos = (mouse_pos[0] // 32, (mouse_pos[1] - 64) // 32)
                    model.character_start_pos = (mouse_pos[0] // 32, (mouse_pos[1] - 64) // 32)
                    model.character_current_pos = (mouse_pos[0] // 32, (mouse_pos[1] - 64) // 32)
                    self.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = view.lvl_val
                    self.save_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = self.save_val
                    model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = view.lvl_val
                if view.obj_select != 10:
                    self.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = view.lvl_val
                    self.save_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = self.save_val
                    model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = view.lvl_val
                model.change_in_game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = True

            if 544 < mouse_pos[0] < 628 and 16 < mouse_pos[1] < 48:
                if model.character_start_pos != (-1, -1) and model.num_batteries > 0:
                    self.paused = False
                    self.is_there_input = True

            if 560 < mouse_pos[1] < 592:
                if 8 < mouse_pos[0] < 92:
                    self.game_map = self.floor_init()
                    model.game_map = model.floor_init()
                    for x in range(len(self.game_map)):
                        for y in range(len(self.game_map[x])):
                            self.save_map[x][y] = 0
                    self.is_there_input = True
                    model.set_change_in_game_map(True)
                    self.saved = False
                    self.verified = False
                    self.num_batteries = 0
                    model.num_batteries = 0
                    self.character_start_pos = (-1, -1)
                    model.character_start_pos = (-1, -1)

                if self.verified and 544 < mouse_pos[0] < 628 and not self.saved:
                    self.saved = True
                    if len(sys.argv) > 1:
                        with open('custom_levels/'+sys.argv[1], 'w', newline='') as level_file:
                            level_writer = csv.writer(level_file, delimiter=',')
                            level_writer.writerow(
                                [self.character_start_pos[0], self.character_start_pos[1], self.num_batteries])
                            for x in range(len(self.save_map)):
                                for y in range(len(self.save_map[x])):
                                    if self.save_map[x][y] != 0:
                                        level_writer.writerow([x, y, self.save_map[x][y]])
                    else:
                        with open('custom_levels/'+model.get_name, 'w', newline='') as level_file:
                            level_writer = csv.writer(level_file, delimiter=',')
                            level_writer.writerow(
                                [self.character_start_pos[0], self.character_start_pos[1], self.num_batteries])
                            for x in range(len(self.save_map)):
                                for y in range(len(self.save_map[x])):
                                    if self.save_map[x][y] != 0:
                                        level_writer.writerow([x, y, self.save_map[x][y]])

        if self.mb_right:
            if 64 < mouse_pos[1] < 544:
                self.saved = False
                self.verified = False
                if model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] is model.battery:
                    self.num_batteries -= 1
                    model.num_batteries -= 1
                if model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] is model.character:
                    self.character_start_pos = (-1, -1)
                    model.character_start_pos = (-1, -1)
                self.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = model.floor
                self.save_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = 0
                model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = model.floor
                model.change_in_game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = True

        keys = pygame.key.get_pressed()  # checking pressed keys
        original_player_input = self.player_input
        number_of_keys_pressed = 0
        if keys[pygame.K_UP]:
            self.is_there_input = True
            self.player_input = 'up'
            number_of_keys_pressed += 1
            # print('up')
        if keys[pygame.K_DOWN]:
            self.is_there_input = True
            self.player_input = 'down'
            number_of_keys_pressed += 1
            # print('down')
        if keys[pygame.K_LEFT]:
            self.is_there_input = True
            self.player_input = 'left'
            number_of_keys_pressed += 1
            # print('left')
        if keys[pygame.K_RIGHT]:
            self.is_there_input = True
            self.player_input = 'right'
            number_of_keys_pressed += 1
            # print('right')
        if number_of_keys_pressed > 1:
            # print('>1')
            self.player_input = original_player_input
        elif number_of_keys_pressed == 0:
            self.player_input = 'nothing'

        return True, self.is_there_input

    def floor_init(self):
        # initialize everything to a floor tile
        game_map = []
        for x in range(GAME_MAP_GRID[0]):
            game_map.append([])
            for y in range(GAME_MAP_GRID[1]):
                game_map[x].append(model.floor)
        return game_map


if __name__ == '__main__':

    # pygame setup
    pygame.init()
    pygame.display.set_caption('Puzzle Game Level Editor')
    controller = PyGameKeyboardController()
    model = Model(controller)
    if GAME_SHOW_SCREEN:
        view = PyGameView(model)

    # loop variable setup
    running = True
    first_update = True

    # display the view initially
    if GAME_SHOW_SCREEN and view.show_view:
        view.draw()
        view.screen.blit(view.surface, (0,0))
        pygame.display.update()

    while running:
        # listen for user input
        if controller.paused:
            model.set_change_in_game_map(False)

        running, there_is_input = controller.handle_input()

        if controller.paused:
            if GAME_SHOW_SCREEN and view.show_view:
                view.draw()
                view.screen.blit(view.surface, (0,0))
                pygame.display.update()

        else:
            if there_is_input or first_update:
                there_is_input, first_update = False, False
                # update the model
                model.update()

                # display the view
                if GAME_SHOW_SCREEN and view.show_view:
                    view.draw()
                    view.screen.blit(view.surface, (0,0))
                    pygame.display.update()

                # reset user input
                controller.player_input = 'nothing'

                # update again if player won or died
                if model.batteries_collected == model.num_batteries or model.maze_reset:
                    model.update()
                    # display the view
                    if GAME_SHOW_SCREEN and view.show_view:
                        view.draw()
                        view.screen.blit(view.surface, (0,0))
                        pygame.display.update()
                    # THIS ONLY WORKS BECAUSE WHEN MODEL.UPDATE
                    # IS CALLED, WINNING OR DEATH WILL BE TRUE
                    # AND THE RETURN STATEMENT WILL KEEP THE
                    # REST OF A NORMAL UPDATE FROM HAPPENING
                    # therefore this is just a way to automatically
                    # load the next level or reload the current level
                    # on win or death without having to click anything
            time.sleep(0.10)  # control frame rate (in seconds)

    pygame.quit()
    sys.exit()
