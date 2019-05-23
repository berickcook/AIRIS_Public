import pygame
import time, sys, csv
from pygame.locals import QUIT, KEYDOWN
from game_objects import *
from airis_stable import AIRIS
from constants import *
from other_useful_functions import pprint
import datetime


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
        self.mind_index_prev = 0
        self.rep_map = []
        w, h = GAME_MAP_GRID
        for x in range(w):
            self.rep_map.append([])
            for y in range(h):
                self.rep_map[x].append(0)

    def draw(self):

        # commented out because we're only updating squares if they change
        # # fill background
        # self.surface.fill(pygame.Color('black'))

        self.draw_game_map()

        self.draw_representation_map()

        # draw control key
        if self.show_controls:
            for n, line in enumerate(PUZZLE_GAME_CONTROL_KEY):
                self.draw_text(line, PUZZLE_GAME_CONTROL_KEY_START[0], \
                    PUZZLE_GAME_CONTROL_KEY_START[1]+14*n, 20)

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

    def draw_representation_map(self):

        # variable setup
        w, h = REP_MAP_GRID # number of positions wide and high
        ms = REP_MAP_START

        if not self.model.controller.bypass and self.model.airis.display_hold:
            self.model.controller.mind_len = len(self.model.airis.display_plan)
            if self.mind_index_prev != self.model.controller.mind_index:
                print('Viewing plan step ' + str(self.model.controller.mind_index) + ' of ' + str(
                    self.model.controller.mind_len - 1) + ' (predicted result)')
                self.mind_index_prev = self.model.controller.mind_index

            # draw each position in the grid
            try:
                for x in range(w):
                    for y in range(h):
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 0:
                            self.rep_map[x][y] = self.model.floor
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 1:
                            self.rep_map[x][y] = self.model.character
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 2:
                            self.rep_map[x][y] = self.model.wall
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 3:
                            self.rep_map[x][y] = self.model.battery
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 4:
                            self.rep_map[x][y] = self.model.door
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 5:
                            self.rep_map[x][y] = self.model.key
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 6:
                            self.rep_map[x][y] = self.model.extinguisher
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 7:
                            self.rep_map[x][y] = self.model.fire
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 8:
                            self.rep_map[x][y] = self.model.right_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 9:
                            self.rep_map[x][y] = self.model.left_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 10:
                            self.rep_map[x][y] = self.model.down_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 11:
                            self.rep_map[x][y] = self.model.up_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 12:
                            self.rep_map[x][y] = self.model.open_door
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 13:
                            self.rep_map[x][y] = self.model.character_on_right_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 14:
                            self.rep_map[x][y] = self.model.character_on_left_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 15:
                            self.rep_map[x][y] = self.model.character_on_down_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 16:
                            self.rep_map[x][y] = self.model.character_on_up_arrow
                        if self.model.airis.models[self.model.airis.display_plan[self.model.controller.mind_index]].vis_env[x][y] == 17:
                            self.rep_map[x][y] = self.model.character_on_open_door

                        self.rep_map[x][y].draw_representation_image(self, x, y)


            except:
                pass
        else:
            for x in range(w):
                for y in range(h):
                    if self.model.change_in_game_map[x][y]:
                        self.model.game_map[x][y].draw_representation_image(self, x, y)

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
    def __init__(self, controller, airis_controlled):
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
        self.player_action = "up"
        
        # AGI setup
        self.screen_input = []
        for x in range(GAME_MAP_GRID[0]):
            self.screen_input.append([])
            for y in range(GAME_MAP_GRID[1]):
                self.screen_input[x].append(0.0)
        self.aux_input = [self.keys_collected, self.extinguishers_collected]
        action_space = ['up', 'down', 'left', 'right', 'nothing']
        #action_output_list = output range of each action [min, max, increment size]
        action_output_list = [
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1],
            [1, 2, 1]
        ]
        self.airis = AIRIS(self.screen_input, self.aux_input, action_space, action_output_list)
        self.airis_controlled = airis_controlled
        if not airis_controlled:
            self.airis.goal_type = 'Observe'
            self.airis.goal_type_default = 'Observe'
        self.time_counter = 0

    # this function updates the model
    def update(self):

        pprint('-------------------------------------------- TIME STEP %d --------------------------------------------'
            % self.time_counter, new_line_start=True, draw_line=False)
        self.time_counter += 1

        self.set_change_in_game_map(False)
        # get user input
        if not self.airis.display_hold or self.controller.bypass:
            self.player_action = 'up'

            if not self.airis_controlled:
                self.player_action = self.get_action()

            # input environment to airis
            self.current_environment()
            if self.airis_controlled:
                self.player_action, _, _ = self.airis.capture_input(
                    self.screen_input,
                    self.aux_input,
                    self.player_action, prior=True)
            else:
                self.airis.capture_input(
                    self.screen_input,
                    self.aux_input,
                    self.player_action, prior=True)
            pprint('ACTION:\t%s' % self.player_action, new_line_start=True, draw_line=False)
            if self.airis.display_hold and not self.controller.bypass:
                self.controller.paused = True
                self.controller.mind_index = 0
                print ('Awaiting plan approval...')

        if not self.controller.paused or self.controller.bypass:
            self.airis.display_hold = False
            # update the model according to the player's input
            self.game_logic(self.player_action)

            # go to next level if player beats the current level
            if self.batteries_collected == self.num_batteries:
                self.get_next_maze()

            # reset the maze if the character dies
            if self.maze_reset:
                self.get_next_maze()

            # input environment to airis
            self.current_environment()
            self.airis.capture_input(
                self.screen_input,
                self.aux_input,
                self.player_action, prior=False)

        # user_input = input()
        # sys.exit()

    # these functions interact with AIRIS
    def get_action(self):
        return self.controller.player_input

    def current_environment(self):

        for x in range(GAME_MAP_GRID[0]):
            for y in range(GAME_MAP_GRID[1]):
                self.screen_input[x][y] = self.game_map[x][y].id

        self.aux_input[0] = self.keys_collected
        self.aux_input[1] = self.extinguishers_collected

    # these functions controls game logic
    def game_logic(self, player_input):

        if player_input != 'nothing':
            if player_input == 'up':
                character_new_pos = \
                (self.character_current_pos[0], \
                self.character_current_pos[1] - 1)
            if player_input == 'down':
                character_new_pos = \
                (self.character_current_pos[0], \
                self.character_current_pos[1] + 1)
            if player_input == 'left':
                character_new_pos = \
                (self.character_current_pos[0] - 1, \
                self.character_current_pos[1])
            if player_input == 'right':
                character_new_pos = \
                (self.character_current_pos[0] + 1, \
                self.character_current_pos[1])

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
                    self.move_character(new_tile, \
                        character_new_pos, self.character_on_right_arrow)

            elif isinstance(new_tile, LeftArrow):
                if player_input != 'right':
                    self.move_character(new_tile, \
                        character_new_pos, self.character_on_left_arrow)

            elif isinstance(new_tile, UpArrow):
                if player_input != 'down':
                    self.move_character(new_tile, \
                        character_new_pos, self.character_on_up_arrow)

            elif isinstance(new_tile, DownArrow):
                if player_input != 'up':
                    self.move_character(new_tile, \
                        character_new_pos, self.character_on_down_arrow)

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
                    self.move_character(new_tile, \
                        character_new_pos, self.character_on_open_door)
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

        self.game_map\
        [self.character_current_pos[0]] \
        [self.character_current_pos[1]] \
        = character_and_floor

        self.change_in_game_map\
        [self.character_current_pos[0]] \
        [self.character_current_pos[1]] \
        = True

        self.game_map\
        [character_old_pos[0]] \
        [character_old_pos[1]] \
        = character_old_floor

        self.change_in_game_map\
        [character_old_pos[0]] \
        [character_old_pos[1]] \
        = True
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

        with open('custom_levels/' + str(self.current_maze) + '.csv', 'r') as File:
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
            self.load_maze();

        except FileNotFoundError:
            self.current_maze = 1
            try:
                self.load_maze();
            except FileNotFoundError:
                print('ERROR: No levels to load!')
                print('Use the included level editor to create levels and place them in /custom_levels')
                print('They must be named 1.csv, 2.csv, 3.csv, ...')
                interrupt = input()
                raise Exception

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
    def draw_wall_row(self, game_map, left, right, y):
        for x in range(left, right+1):
            game_map[x][y] = self.wall
        return game_map
    def draw_wall_col(self, game_map, bottom, top, x):
        for y in range(bottom, top+1):
            game_map[x][y] = self.wall
        return game_map
    def draw_fire_row(self, game_map, left, right, y):
        for x in range(left, right+1):
            game_map[x][y] = self.fire
        return game_map
    def draw_fire_col(self, game_map, bottom, top, x):
        for y in range(bottom, top+1):
            game_map[x][y] = self.fire
        return game_map
    def draw_arrow_row(self, game_map, left, right, y, type):
        for x in range(left, right+1):
            if type == 'r':
                game_map[x][y] = self.right_arrow
            if type == 'l':
                game_map[x][y] = self.left_arrow
            if type == 'u':
                game_map[x][y] = self.up_arrow
            if type == 'd':
                game_map[x][y] = self.down_arrow
        return game_map
    def draw_arrow_col(self, game_map, bottom, top, x, type):
        for y in range(bottom, top+1):
            if type == 'r':
                game_map[x][y] = self.right_arrow
            if type == 'l':
                game_map[x][y] = self.left_arrow
            if type == 'u':
                game_map[x][y] = self.up_arrow
            if type == 'd':
                game_map[x][y] = self.down_arrow
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

        self.paused = False
        self.player_input = 'nothing'
        self.mind_index = 0
        self.mind_action = ''
        self.mind_len = 0
        self.bypass = True

    def handle_input(self):

        is_there_input = False

        for event in pygame.event.get():
            if event.type == QUIT:
                return False, is_there_input
            else:
                if event.type != KEYDOWN:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        print ('mouse interrupt')
                        interrupt = input()
                        #print('mouse position = (%d,%d)') % (mouse_pos[0], mouse_pos[1])

                        if event.button == 4:
                            print('mouse wheel scroll up')
                        elif event.button == 5:
                            print('mouse wheel scroll down')
                        elif event.button == 1:
                            print('mouse left click')
                        elif event.button == 3:
                            print('mouse right click')
                        else:
                            print('event.button = %d' % event.button)
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print('Plan approved!')
                elif event.key == pygame.K_k:
                    view.show_controls = not view.show_controls
                elif event.key == pygame.K_v:
                    view.show_view = not view.show_view

        keys = pygame.key.get_pressed()  # checking pressed keys
        original_player_input = self.player_input
        number_of_keys_pressed = 0
        if keys[pygame.K_UP]:
            is_there_input = True
            self.player_input = 'up'
            number_of_keys_pressed += 1
            if airis_controlled:
                self.bypass = False
            # print('up')
        if keys[pygame.K_DOWN]:
            is_there_input = True
            self.player_input = 'down'
            number_of_keys_pressed += 1
            if airis_controlled:
                self.bypass = True
            # print('down')
        if keys[pygame.K_LEFT]:
            is_there_input = True
            self.player_input = 'left'
            number_of_keys_pressed += 1
            if airis_controlled:
                if self.mind_index > 0:
                    self.mind_index -= 1
            # print('left')
        if keys[pygame.K_RIGHT]:
            is_there_input = True
            self.player_input = 'right'
            number_of_keys_pressed += 1
            if airis_controlled:
                if self.mind_index < self.mind_len-1:
                    self.mind_index += 1
            # print('right')
        if number_of_keys_pressed > 1:
            # print('>1')
            self.player_input = original_player_input
        elif number_of_keys_pressed == 0:
            self.player_input = 'nothing'

        return True, is_there_input


if __name__ == '__main__':

    # pygame setup
    airis_controlled = True
    pygame.init()
    pygame.display.set_caption('Airis '+str(id(pygame)))
    controller = PyGameKeyboardController()
    model = Model(controller, airis_controlled)
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

    # if airis_controlled:
    #     print ('Press any key to begin')
    #     interrupt = input()

    while running:

        # # output frame rate
        # iterations += 1
        # if time.time() - start_time > 1:
        #     start_time += 1
        #     print '%s fps' % iterations
        #     iterations = 0

        # listen for user input
        running, there_is_input = controller.handle_input()

        # if theres user input
        if model.airis_controlled or there_is_input or first_update:
            there_is_input, first_update = False, False
            # update the model
            if not controller.paused:
                model.update()

            # display the view
            if GAME_SHOW_SCREEN and view.show_view:
                view.draw()
                view.screen.blit(view.surface, (0,0))
                pygame.display.update()

            # reset user input
            controller.player_input = 'nothing'

            # update again if player won or died
            if not controller.paused:
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


        time.sleep(0.10) # control frame rate (in seconds)


    pygame.quit()
    sys.exit()
