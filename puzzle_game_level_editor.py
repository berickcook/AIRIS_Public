import pygame
import time, sys, csv
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
        self.lvl_val = 0

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

        pygame.draw.rect(self.surface, 8421504, pygame.Rect(2,2,636,60))
        pygame.draw.rect(self.surface, 8421504, pygame.Rect(2,546,636,60))

        pygame.draw.rect(self.surface, 12632256, pygame.Rect(4,4,632,56))
        pygame.draw.rect(self.surface, 12632256, pygame.Rect(4,548,632,56))

        for i in range(11):
            if self.obj_select == i:
                pygame.draw.rect(self.surface, 16777215, pygame.Rect(8+(48*i), 8, 48, 48))
            else:
                pygame.draw.rect(self.surface, 8421504, pygame.Rect(8+(48*i), 8, 48, 48))

            pygame.draw.rect(self.surface, 0, pygame.Rect(8+(48*i),8,48,48), 1)
            self.surface.blit(self.sprites[i], ((16*(i+1))+(32*i), 16))
        self.draw_game_map()

        # draw control key
        if self.show_controls:
            for n, line in enumerate(PUZZLE_GAME_CONTROL_KEY):
                self.draw_text(line, PUZZLE_GAME_CONTROL_KEY_START[0], PUZZLE_GAME_CONTROL_KEY_START[1]+14*n, 20)

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

    def draw_text(self, text, x, y, size, color = (100, 100, 100)):
        basicfont = pygame.font.SysFont(None, size)
        text_render = basicfont.render(
            text, True, color)
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

    # this function updates the model
    def update(self):

        self.set_change_in_game_map(False)

        # get user input
        player_action = self.get_action()

        # update the game according to the player's input
        self.game_logic(player_action)

        # go to next level if player beats the current level
        if self.batteries_collected == self.num_batteries:
            self.get_next_maze()

        # reset the maze if the character dies
        if self.maze_reset:
            self.get_next_maze()

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
            self.character_start_pos = (0, 0)
            self.character_current_pos = (0, 0)
            self.character_current_floor = self.floor

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

    def handle_input(self):

        is_there_input = False

        for event in pygame.event.get():
            if event.type == QUIT:
                return False, is_there_input
            else:
                if event.type != KEYDOWN:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()

                        print('mouse position = ',mouse_pos[0], mouse_pos[1])

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
                    self.paused = not self.paused
                elif event.key == pygame.K_k:
                    view.show_controls = not view.show_controls
                elif event.key == pygame.K_v:
                    view.show_view = not view.show_view

        mouse_pos = pygame.mouse.get_pos()
        if self.mb_left:
            if 8 <= mouse_pos[0] <= 528 and 8 <= mouse_pos[1] <= 56:
                view.obj_select = (mouse_pos[0] - 8) // 48
        if self.mb_right:
            if 64 < mouse_pos[1] < 544:
                model.game_map[mouse_pos[0] // 32][(mouse_pos[1] - 64) // 32] = model.floor

        keys = pygame.key.get_pressed()  # checking pressed keys
        original_player_input = self.player_input
        number_of_keys_pressed = 0
        if keys[pygame.K_UP]:
            is_there_input = True
            self.player_input = 'up'
            number_of_keys_pressed += 1
            # print('up')
        if keys[pygame.K_DOWN]:
            is_there_input = True
            self.player_input = 'down'
            number_of_keys_pressed += 1
            # print('down')
        if keys[pygame.K_LEFT]:
            is_there_input = True
            self.player_input = 'left'
            number_of_keys_pressed += 1
            # print('left')
        if keys[pygame.K_RIGHT]:
            is_there_input = True
            self.player_input = 'right'
            number_of_keys_pressed += 1
            # print('right')
        if number_of_keys_pressed > 1:
            # print('>1')
            self.player_input = original_player_input
        elif number_of_keys_pressed == 0:
            self.player_input = 'nothing'

        return True, is_there_input


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
    # iterations = 0
    first_update = True

    # display the view initially
    if GAME_SHOW_SCREEN and view.show_view:
        view.draw()
        view.screen.blit(view.surface, (0,0))
        pygame.display.update()

    while running:

        # listen for user input
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
