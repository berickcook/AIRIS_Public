import time, sys, os
from pygame.locals import QUIT, KEYDOWN
from game_objects import *
from constants import *
from airis_stable import AIRIS
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
        self.counter = len(os.listdir('./screens'))
        self.log = 0

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
        self.counter += 1

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

        # draw each position in the grid
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
    def __init__(self, controller, ai_controlled):
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
        self.mover_list = []
        self.mover_pos = []
        self.mover_dir = []
        self.make_singletons()
        self.current_maze = 0
        self.get_next_maze()
        self.plan_made = False
        self.player_action = None
        self.state = None
        self.final_action_step = False

        # AGI setup
        self.screen_input = []
        for x in range(GAME_MAP_GRID[0]):
            self.screen_input.append([])
            for y in range(GAME_MAP_GRID[1]):
                self.screen_input[x].append(0.0)
        self.aux_input = [self.keys_collected, self.extinguishers_collected, 0]
        self.action_space = ['up', 'down', 'left', 'right']
        self.ai_controlled = ai_controlled
        self.time_counter = 0
        self.airis = AIRIS(self.aux_input, self.screen_input, self.action_space)
        self.airis.load_knowledge('Knowledge.npy')
        if not ai_controlled:
            self.airis.observe_mode = True
        self.airis.given_goal_state = [[[2, '+']], []]

    # this function updates the model
    def update(self):

        self.time_counter += 1

        self.set_change_in_game_map(False)

        player_action = 'nothing'

        level_change = False
        player_death = False

        # get user input
        if not self.ai_controlled:
            player_action = self.get_action()

        # set environment values to current and output to ai
        self.current_environment()

        if not self.plan_made:
            if self.ai_controlled:
                self.player_action, self.state = self.airis.capture_input(self.aux_input, self.screen_input, None, None, True)
            else:
                act, state = self.airis.capture_input(self.aux_input, self.screen_input, player_action, None, True)

            self.plan_made = True
            if self.controller.approval_mode:
                self.controller.paused = True

        else:
            if self.player_action:
                player_action = self.player_action
                state = self.state
                self.player_action = None
                self.state = None
            else:
                if self.ai_controlled:
                    player_action, state = self.airis.capture_input(self.aux_input, self.screen_input, None, None, True)
                else:
                    act, state = self.airis.capture_input(self.aux_input, self.screen_input, player_action, None, True)

            # update the game according to the player's input
            self.game_logic(player_action)

            # output post-action environment to ai
            self.current_environment()

            # go to next level if player beats the current level
            if self.batteries_collected == self.num_batteries:
                level_change = True
                self.airis.capture_input(self.aux_input, self.screen_input, player_action, state, False)
                self.get_next_maze()

            # reset the maze if the character dies
            if self.maze_reset:
                player_death = True
                self.aux_input[2] -= 1
                self.airis.capture_input(self.aux_input, self.screen_input, player_action, state, False)
                self.get_next_maze()

            if not level_change and not player_death:
                self.airis.capture_input(self.aux_input, self.screen_input, player_action, state, False)
            else:
                self.airis.action_plan = []
                self.airis.pos_change_2D = []

            self.airis.save_knowledge('Knowledge.npy')

            if self.airis.action_plan:
                self.plan_made = True
            else:
                self.plan_made = False

            if not controller.approval_mode:
                self.plan_made = True

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

        for i, obj in enumerate(self.mover_list):
            if self.mover_dir[i] == 'L':
                check_tile = self.game_map[self.mover_pos[i][0] - 1][self.mover_pos[i][1]]
                if isinstance(check_tile, Floor):
                    self.game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = self.floor
                    self.change_in_game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = True
                    self.game_map[self.mover_pos[i][0] - 1][self.mover_pos[i][1]] = self.mover_list[i]
                    self.change_in_game_map[self.mover_pos[i][0] - 1][self.mover_pos[i][1]] = True
                    self.mover_pos[i] = [self.mover_pos[i][0] - 1, self.mover_pos[i][1]]

                if isinstance(check_tile, Wall):
                    self.mover_dir[i] = 'R'
                    self.game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = self.floor
                    self.change_in_game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = True
                    self.game_map[self.mover_pos[i][0] + 1][self.mover_pos[i][1]] = self.mover_list[i]
                    self.change_in_game_map[self.mover_pos[i][0] + 1][self.mover_pos[i][1]] = True
                    self.mover_pos[i] = [self.mover_pos[i][0] + 1, self.mover_pos[i][1]]

            elif self.mover_dir[i] == 'R':
                check_tile = self.game_map[self.mover_pos[i][0] + 1][self.mover_pos[i][1]]
                if isinstance(check_tile, Floor):
                    self.game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = self.floor
                    self.change_in_game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = True
                    self.game_map[self.mover_pos[i][0] + 1][self.mover_pos[i][1]] = self.mover_list[i]
                    self.change_in_game_map[self.mover_pos[i][0] + 1][self.mover_pos[i][1]] = True
                    self.mover_pos[i] = [self.mover_pos[i][0] + 1, self.mover_pos[i][1]]

                if isinstance(check_tile, Wall):
                    self.mover_dir[i] = 'L'
                    self.game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = self.floor
                    self.change_in_game_map[self.mover_pos[i][0]][self.mover_pos[i][1]] = True
                    self.game_map[self.mover_pos[i][0] - 1][self.mover_pos[i][1]] = self.mover_list[i]
                    self.change_in_game_map[self.mover_pos[i][0] - 1][self.mover_pos[i][1]] = True
                    self.mover_pos[i] = [self.mover_pos[i][0] - 1, self.mover_pos[i][1]]

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
                    self.move_character(new_tile, character_new_pos, self.character)
                    self.character_current_floor = self.floor
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

            elif isinstance(new_tile, Mover):
                self.reset_maze()
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
        self.aux_input[2] += 1
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
    def test_maze(self):

        # initialize everything to a floor tile
        game_map = self.floor_init()

        # test every type of tile
        game_map[0][1] = self.character
        game_map[0][2] = self.floor
        game_map[0][3] = self.wall
        game_map[0][4] = self.fire
        game_map[0][5] = self.extinguisher
        game_map[0][6] = self.battery
        game_map[0][7] = self.key
        game_map[0][8] = self.door
        game_map[0][9] = self.open_door
        game_map[1][1] = self.right_arrow
        game_map[1][2] = self.left_arrow
        game_map[1][3] = self.down_arrow
        game_map[1][4] = self.up_arrow
        game_map[1][5] = self.character_on_right_arrow
        game_map[1][6] = self.character_on_left_arrow
        game_map[1][7] = self.character_on_down_arrow
        game_map[1][8] = self.character_on_up_arrow
        game_map[1][9] = self.character_on_open_door

        self.num_batteries = 1

        self.game_map = game_map
        self.character_start_pos = (0,1)
        self.character_current_pos = (0,1)
        self.character_current_floor = self.floor
    def maze1(self):

        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 4, 16, 2)
        game_map = self.draw_wall_row(game_map, 4, 16, 12)
        game_map = self.draw_wall_row(game_map, 7, 15, 5)
        game_map = self.draw_wall_col(game_map, 3, 11, 4)
        game_map = self.draw_wall_col(game_map, 3, 11, 16)
        game_map = self.draw_wall_col(game_map, 8, 11, 8)
        game_map = self.draw_wall_col(game_map, 8, 11, 12)
        game_map[5][8] = self.wall
        game_map[7][8] = self.wall
        game_map[9][8] = self.wall
        game_map[11][8] = self.wall
        game_map[13][8] = self.wall
        game_map[15][8] = self.wall

        # initialize all the batteries
        game_map[15][3] = self.battery
        game_map[6][10] = self.battery
        game_map[14][10] = self.battery
        self.num_batteries = 3

        # initialize the character
        game_map[10][10] = self.character
        self.character_start_pos = (10, 10)
        self.character_current_pos = (10, 10)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze2(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 5, 13, 1)
        game_map = self.draw_wall_row(game_map, 2, 5, 5)
        game_map = self.draw_wall_row(game_map, 2, 5, 9)
        game_map = self.draw_wall_row(game_map, 5, 13, 13)
        game_map = self.draw_wall_col(game_map, 5, 9, 2)
        game_map = self.draw_wall_col(game_map, 1, 5, 5)
        game_map = self.draw_wall_col(game_map, 9, 13, 5)
        game_map = self.draw_wall_col(game_map, 4, 10, 8)
        game_map = self.draw_wall_col(game_map, 4, 6, 10)
        game_map = self.draw_wall_col(game_map, 8, 10, 10)
        game_map = self.draw_wall_col(game_map, 1, 13, 13)

        # initialize all the arrows
        game_map = self.draw_arrow_row(game_map, 6, 7, 5, 'd')
        game_map = self.draw_arrow_row(game_map, 11, 12, 4, 'u')
        game_map[9][4] = self.up_arrow
        game_map[10][7] = self.left_arrow
        game_map[9][10] = self.up_arrow

        # initialize all the batteries
        game_map[6][4] = self.battery
        game_map[9][2] = self.battery
        game_map[9][7] = self.battery
        game_map[12][5] = self.battery
        self.num_batteries = 4

        # initialize the character
        game_map[4][7] = self.character
        self.character_start_pos = (4, 7)
        self.character_current_pos = (4, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze3(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 3, 16, 5)
        game_map = self.draw_wall_row(game_map, 3, 16, 9)
        game_map = self.draw_wall_col(game_map, 5, 9, 3)
        game_map = self.draw_wall_col(game_map, 5, 9, 16)

        # initialize all the arrows
        game_map[7][6] = self.up_arrow
        game_map[8][6] = self.right_arrow
        game_map[9][6] = self.down_arrow
        game_map[10][6] = self.right_arrow
        game_map[11][6] = self.right_arrow
        game_map[12][6] = self.up_arrow
        game_map[7][7] = self.right_arrow
        game_map[8][7] = self.right_arrow
        game_map[9][7] = self.right_arrow
        game_map[10][7] = self.left_arrow
        game_map[11][7] = self.right_arrow
        game_map[12][7] = self.right_arrow
        game_map[7][8] = self.right_arrow
        game_map[8][8] = self.left_arrow
        game_map[9][8] = self.right_arrow
        game_map[10][8] = self.right_arrow
        game_map[11][8] = self.up_arrow
        game_map[12][8] = self.right_arrow

        # initialize all the batteries
        game_map[5][7] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[14][7] = self.character
        self.character_start_pos = (14, 7)
        self.character_current_pos = (14, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze4(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 3, 17, 0)
        game_map = self.draw_wall_row(game_map, 5, 8, 5)
        game_map = self.draw_wall_row(game_map, 12, 15, 5)
        game_map = self.draw_wall_row(game_map, 5, 8, 9)
        game_map = self.draw_wall_row(game_map, 12, 15, 9)
        game_map = self.draw_wall_row(game_map, 3, 17, 14)
        game_map = self.draw_wall_col(game_map, 0, 14, 3)
        game_map = self.draw_wall_col(game_map, 2, 5, 8)
        game_map = self.draw_wall_col(game_map, 9, 12, 8)
        game_map = self.draw_wall_col(game_map, 2, 5, 12)
        game_map = self.draw_wall_col(game_map, 9, 12, 12)
        game_map = self.draw_wall_col(game_map, 0, 14, 17)

        # initialize all the arrows
        game_map[8][1] = self.right_arrow
        game_map[12][1] = self.right_arrow
        game_map = self.draw_arrow_row(game_map, 9, 11, 2, 'r')
        game_map[4][5] = self.up_arrow
        game_map[16][5] = self.down_arrow
        game_map = self.draw_arrow_col(game_map, 6, 8, 5, 'r')
        game_map = self.draw_arrow_col(game_map, 6, 8, 15, 'l')
        game_map[4][9] = self.up_arrow
        game_map[16][9] = self.down_arrow
        game_map = self.draw_arrow_row(game_map, 9, 11, 12, 'u')
        game_map[8][13] = self.left_arrow
        game_map[12][13] = self.left_arrow

        # initialize all the batteries
        game_map[6][3] = self.battery
        game_map[14][3] = self.battery
        game_map[6][11] = self.battery
        game_map[14][11] = self.battery
        self.num_batteries = 4

        # initialize the character
        game_map[10][7] = self.character
        self.character_start_pos = (10, 7)
        self.character_current_pos = (10, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze5(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 1, 18, 1)
        game_map = self.draw_wall_row(game_map, 1, 3, 3)
        game_map = self.draw_wall_row(game_map, 7, 8, 3)
        game_map = self.draw_wall_row(game_map, 14, 16, 3)
        game_map = self.draw_wall_row(game_map, 1, 2, 5)
        game_map = self.draw_wall_row(game_map, 4, 6, 5)
        game_map = self.draw_wall_row(game_map, 14, 16, 5)
        game_map = self.draw_wall_row(game_map, 10, 12, 6)
        game_map = self.draw_wall_row(game_map, 1, 4, 7)
        game_map = self.draw_wall_row(game_map, 3, 8, 9)
        game_map = self.draw_wall_row(game_map, 13, 15, 9)
        game_map = self.draw_wall_row(game_map, 3, 5, 11)
        game_map = self.draw_wall_row(game_map, 11, 14, 11)
        game_map = self.draw_wall_row(game_map, 1, 18, 13)
        game_map = self.draw_wall_col(game_map, 1, 13, 1)
        game_map = self.draw_wall_col(game_map, 9, 11, 3)
        game_map = self.draw_wall_col(game_map, 1, 3, 5)
        game_map = self.draw_wall_col(game_map, 5, 7, 6)
        game_map = self.draw_wall_col(game_map, 11, 13, 7)
        game_map = self.draw_wall_col(game_map, 3, 9, 8)
        game_map = self.draw_wall_col(game_map, 11, 13, 9)
        game_map = self.draw_wall_col(game_map, 3, 6, 10)
        game_map = self.draw_wall_col(game_map, 8, 9, 10)
        game_map = self.draw_wall_col(game_map, 9, 11, 11)
        game_map = self.draw_wall_col(game_map, 3, 4, 12)
        game_map = self.draw_wall_col(game_map, 6, 7, 12)
        game_map = self.draw_wall_col(game_map, 7, 9, 13)
        game_map = self.draw_wall_col(game_map, 3, 5, 14)
        game_map = self.draw_wall_col(game_map, 5, 9, 15)
        game_map = self.draw_wall_col(game_map, 7, 9, 17)
        game_map = self.draw_wall_col(game_map, 1, 13, 18)
        game_map[16][11] = self.wall

        # initialize all the arrows
        game_map[10][2] = self.left_arrow
        game_map[5][4] = self.left_arrow
        game_map[13][5] = self.up_arrow
        game_map[10][7] = self.right_arrow
        game_map[7][10] = self.left_arrow
        game_map[14][10] = self.right_arrow
        game_map[14][12] = self.right_arrow

        # initialize all the batteries
        game_map[2][4] = self.battery
        game_map[7][4] = self.battery
        game_map[15][4] = self.battery
        game_map[11][8] = self.battery
        game_map[14][8] = self.battery
        game_map[4][10] = self.battery
        game_map[8][12] = self.battery
        game_map[17][12] = self.battery
        self.num_batteries = 8

        # initialize the character
        game_map[2][2] = self.character
        self.character_start_pos = (2, 2)
        self.character_current_pos = (2, 2)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze6(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 6, 14, 2)
        game_map = self.draw_wall_row(game_map, 6, 11, 6)
        game_map = self.draw_wall_row(game_map, 13, 14, 6)
        game_map = self.draw_wall_row(game_map, 6, 14, 11)
        game_map = self.draw_wall_col(game_map, 2, 11, 6)
        game_map = self.draw_wall_col(game_map, 2, 6, 10)
        game_map = self.draw_wall_col(game_map, 2, 11, 14)

        # initialize all the doors
        game_map[8][6] = self.door

        # initialize all the keys
        game_map[12][4] = self.key

        # initialize all the batteries
        game_map[8][4] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[10][9] = self.character
        self.character_start_pos = (10, 9)
        self.character_current_pos = (10, 9)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze7(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 7, 13, 1)
        game_map = self.draw_wall_row(game_map, 7, 13, 12)
        game_map = self.draw_wall_col(game_map, 1, 12, 7)
        game_map = self.draw_wall_col(game_map, 1, 12, 13)

        # initialize all the fire
        game_map[8][2] = self.fire
        game_map[9][2] = self.fire
        game_map[10][2] = self.fire
        game_map[11][3] = self.fire
        game_map[9][4] = self.fire
        game_map[10][5] = self.fire
        game_map[8][6] = self.fire
        game_map[11][6] = self.fire
        game_map[9][7] = self.fire
        game_map[12][7] = self.fire
        game_map[10][8] = self.fire
        game_map[8][9] = self.fire
        game_map[12][9] = self.fire

        # initialize all the batteries
        game_map[11][2] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[10][10] = self.character
        self.character_start_pos = (10, 10)
        self.character_current_pos = (10, 10)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze8(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 2, 17, 2)
        game_map = self.draw_wall_row(game_map, 5, 18, 6)
        game_map = self.draw_wall_row(game_map, 5, 18, 8)
        game_map = self.draw_wall_row(game_map, 2, 17, 12)
        game_map = self.draw_wall_col(game_map, 2, 12, 2)
        game_map = self.draw_wall_col(game_map, 2, 6, 5)
        game_map = self.draw_wall_col(game_map, 8, 12, 5)
        game_map = self.draw_wall_col(game_map, 2, 6, 9)
        game_map = self.draw_wall_col(game_map, 8, 9, 9)
        game_map = self.draw_wall_col(game_map, 11, 12, 9)
        game_map = self.draw_wall_col(game_map, 2, 6, 13)
        game_map = self.draw_wall_col(game_map, 8, 12, 13)
        game_map = self.draw_wall_col(game_map, 2, 12, 17)
        game_map = self.draw_wall_col(game_map, 6, 8, 18)

        # initialize all the fire
        game_map[17][7] = self.fire

        # initialize all the doors
        game_map[6][6] = self.door
        game_map[11][6] = self.door
        game_map[16][6] = self.door
        game_map[6][8] = self.door
        game_map[11][8] = self.door
        game_map[16][8] = self.door

        # initialize all the keys
        game_map[7][4] = self.key
        game_map[15][4] = self.key
        game_map[3][11] = self.key
        game_map[4][11] = self.key
        game_map[7][10] = self.key
        game_map[11][10] = self.key

        # initialize all the batteries
        #game_map[3][3] = self.battery
        game_map[11][4] = self.battery
        game_map[15][10] = self.battery
        self.num_batteries = 2

        # initialize the character
        game_map[3][7] = self.character
        self.character_start_pos = (3, 7)
        self.character_current_pos = (3, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze9(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 2, 12, 1)
        game_map = self.draw_wall_row(game_map, 12, 16, 4)
        game_map = self.draw_wall_row(game_map, 2, 8, 5)
        game_map = self.draw_wall_row(game_map, 12, 16, 8)
        game_map = self.draw_wall_row(game_map, 8, 12, 12)
        game_map = self.draw_wall_col(game_map, 1, 5, 2)
        game_map = self.draw_wall_col(game_map, 5, 12, 8)
        game_map = self.draw_wall_col(game_map, 1, 4, 12)
        game_map = self.draw_wall_col(game_map, 8, 12, 12)
        game_map = self.draw_wall_col(game_map, 4, 8, 16)

        # initialize all the fire
        game_map = self.draw_fire_row(game_map, 9, 11, 8)
        game_map = self.draw_fire_col(game_map, 5, 7, 12)
        game_map = self.draw_fire_col(game_map, 5, 7, 13)

        # initialize all the extinguishers
        game_map[10][3] = self.extinguisher
        game_map[9][10] = self.extinguisher
        game_map[11][10] = self.extinguisher

        # initialize all the batteries
        game_map[15][6] = self.battery
        game_map[10][10] = self.battery
        self.num_batteries = 2

        # initialize the character
        game_map[4][3] = self.character
        self.character_start_pos = (4, 3)
        self.character_current_pos = (4, 3)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze10(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 6, 14, 2)
        game_map = self.draw_wall_row(game_map, 10, 14, 6)
        game_map = self.draw_wall_row(game_map, 13, 14, 6)
        game_map = self.draw_wall_row(game_map, 6, 14, 10)
        game_map = self.draw_wall_col(game_map, 2, 10, 6)
        game_map = self.draw_wall_col(game_map, 2, 6, 10)
        game_map = self.draw_wall_col(game_map, 2, 10, 14)
        game_map[8][6] = self.wall

        # initialize all the doors
        game_map[10][4] = self.door

        # initialize all the keys
        game_map[12][8] = self.key

        # initialize all the extinguishers
        game_map[8][4] = self.extinguisher

        # initialize all the fire
        game_map[11][4] = self.fire

        # initialize all the batteries
        game_map[12][4] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[8][8] = self.character
        self.character_start_pos = (8, 8)
        self.character_current_pos = (8, 8)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze11(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 9, 13, 1)
        game_map = self.draw_wall_row(game_map, 5, 7, 2)
        game_map = self.draw_wall_row(game_map, 1, 18, 5)
        game_map = self.draw_wall_row(game_map, 1, 18, 9)
        game_map = self.draw_wall_row(game_map, 5, 7, 12)
        game_map = self.draw_wall_row(game_map, 9, 13, 13)
        game_map = self.draw_wall_col(game_map, 5, 9, 1)
        game_map = self.draw_wall_col(game_map, 2, 5, 5)
        game_map = self.draw_wall_col(game_map, 9, 12, 5)
        game_map = self.draw_wall_col(game_map, 2, 5, 7)
        game_map = self.draw_wall_col(game_map, 9, 12, 7)
        game_map = self.draw_wall_col(game_map, 1, 5, 9)
        game_map = self.draw_wall_col(game_map, 9, 13, 9)
        game_map = self.draw_wall_col(game_map, 1, 5, 13)
        game_map = self.draw_wall_col(game_map, 9, 13, 13)
        game_map = self.draw_wall_col(game_map, 5, 9, 14)
        game_map = self.draw_wall_col(game_map, 5, 9, 18)

        # initialize all the fire
        game_map = self.draw_fire_col(game_map, 6, 8, 12)
        game_map = self.draw_fire_col(game_map, 6, 8, 13)
        game_map[6][5] = self.fire
        game_map[15][7] = self.fire

        # initialize all the extinguishers
        game_map[11][2] = self.extinguisher
        game_map[8][6] = self.extinguisher
        game_map[6][11] = self.extinguisher
        game_map[11][12] = self.extinguisher

        # initialize all the doors
        game_map[11][5] = self.door
        game_map[14][7] = self.door
        game_map[6][9] = self.door
        game_map[11][9] = self.door

        # initialize all the keys
        game_map[6][3] = self.key
        game_map[11][3] = self.key
        game_map[8][8] = self.key
        game_map[11][11] = self.key

        # initialize all the batteries
        game_map[17][7] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[3][7] = self.character
        self.character_start_pos = (3, 7)
        self.character_current_pos = (3, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze12(self):

        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 1, 18, 1)
        game_map = self.draw_wall_row(game_map, 1, 5, 5)
        game_map = self.draw_wall_row(game_map, 10, 18, 5)
        game_map = self.draw_wall_row(game_map, 1, 5, 9)
        game_map = self.draw_wall_row(game_map, 10, 18, 9)
        game_map = self.draw_wall_row(game_map, 1, 18, 13)
        game_map = self.draw_wall_col(game_map, 1, 13, 1)
        game_map = self.draw_wall_col(game_map, 5, 9, 5)
        game_map = self.draw_wall_col(game_map, 1, 13, 10)
        game_map = self.draw_wall_col(game_map, 1, 13, 14)
        game_map = self.draw_wall_col(game_map, 1, 13, 18)

        # initialize all the fire
        game_map = self.draw_fire_col(game_map, 2, 4, 5)
        game_map = self.draw_fire_col(game_map, 2, 4, 13)

        # initialize all the arrows
        game_map = self.draw_arrow_row(game_map, 11, 13, 9, 'u')
        game_map = self.draw_arrow_col(game_map, 2, 4, 10, 'r')
        game_map = self.draw_arrow_col(game_map, 6, 8, 14, 'r')
        game_map[10][7] = self.left_arrow
        game_map[15][9] = self.down_arrow
        game_map[16][9] = self.down_arrow
        game_map[17][9] = self.left_arrow
        game_map[10][11] = self.right_arrow
        game_map[14][10] = self.left_arrow
        game_map[14][11] = self.left_arrow
        game_map[14][12] = self.up_arrow

        # initialize all the extinguishers
        game_map[3][4] = self.extinguisher
        game_map[3][7] = self.extinguisher

        # initialize all the doors
        game_map[14][3] = self.door
        game_map[3][9] = self.door

        # initialize all the keys
        game_map[3][2] = self.key
        game_map[16][7] = self.key

        # initialize all the batteries
        game_map[16][3] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[3][11] = self.character
        self.character_start_pos = (3, 11)
        self.character_current_pos = (3, 11)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze13(self):
        # initialize everything to a floor tile
        game_map = self.floor_init()

        # initialize all the walls
        game_map = self.draw_wall_row(game_map, 0, 19, 0)
        game_map = self.draw_wall_row(game_map, 0, 4, 3)
        game_map = self.draw_wall_row(game_map, 8, 19, 4)
        game_map = self.draw_wall_row(game_map, 0, 8, 6)
        game_map = self.draw_wall_row(game_map, 0, 8, 8)
        game_map = self.draw_wall_row(game_map, 10, 19, 8)
        game_map = self.draw_wall_row(game_map, 8, 12, 10)
        game_map = self.draw_wall_row(game_map, 16, 19, 11)
        game_map = self.draw_wall_row(game_map, 0, 8, 12)
        game_map = self.draw_wall_row(game_map, 0, 19, 14)
        game_map = self.draw_wall_col(game_map, 0, 14, 0)
        game_map = self.draw_wall_col(game_map, 0, 6, 4)
        game_map = self.draw_wall_col(game_map, 8, 14, 4)
        game_map = self.draw_wall_col(game_map, 0, 14, 8)
        game_map = self.draw_wall_col(game_map, 4, 10, 10)
        game_map = self.draw_wall_col(game_map, 0, 4, 12)
        game_map = self.draw_wall_col(game_map, 10, 14, 12)
        game_map = self.draw_wall_col(game_map, 4, 8, 14)
        game_map = self.draw_wall_col(game_map, 11, 14, 16)
        game_map = self.draw_wall_col(game_map, 0, 14, 19)

        # initialize all the fire
        game_map[2][8] = self.fire

        # initialize all the extinguishers
        game_map[1][13] = self.extinguisher

        # initialize all the doors
        game_map[4][1] = self.door
        game_map[8][2] = self.door
        game_map[12][2] = self.door
        game_map[13][4] = self.door
        game_map[15][4] = self.door
        game_map[2][6] = self.door
        game_map[6][6] = self.door
        game_map[8][7] = self.door
        game_map[6][8] = self.door
        game_map[18][8] = self.door
        game_map[12][12] = self.door
        game_map[4][13] = self.door
        game_map[8][13] = self.door
        game_map[16][13] = self.door

        # initialize all the keys
        game_map[1][1] = self.key
        game_map[1][2] = self.key
        game_map[17][2] = self.key
        game_map[1][4] = self.key
        game_map[3][4] = self.key
        game_map[9][5] = self.key
        game_map[11][5] = self.key
        game_map[11][7] = self.key
        game_map[5][9] = self.key
        game_map[7][9] = self.key
        game_map[9][9] = self.key
        game_map[11][9] = self.key
        game_map[6][11] = self.key
        game_map[18][13] = self.key

        # initialize all the batteries
        game_map[2][10] = self.battery
        self.num_batteries = 1

        # initialize the character
        game_map[9][7] = self.character
        self.character_start_pos = (9, 7)
        self.character_current_pos = (9, 7)
        self.character_current_floor = self.floor

        self.game_map = game_map
    def maze_move(self):
        game_map = self.floor_init()

        game_map = self.draw_wall_row(game_map, 2, 12, 2)
        game_map = self.draw_wall_row(game_map, 2, 12, 12)
        game_map = self.draw_wall_col(game_map, 2, 12, 2)
        game_map = self.draw_wall_col(game_map, 2, 12, 12)

        game_map[3][3] = self.battery
        self.num_batteries = 1

        game_map[5][5] = self.character
        self.character_start_pos = (5, 5)
        self.character_current_pos = (5, 5)
        self.character_current_floor = self.floor

        self.mover_list.append(self.mover)
        self.mover_pos.append([8,8])
        self.mover_dir.append('L')

        game_map[8][8] = self.mover_list[0]

        self.game_map = game_map

    def get_next_maze(self):

        self.set_change_in_game_map(True)

        self.current_maze += 1

        self.batteries_collected = 0
        self.extinguishers_collected = 0
        self.keys_collected = 0
        self.maze_reset = False
        self.mover_list = []
        self.mover_pos = []
        self.mover_dir = []

        if self.current_maze == 1:  return self.maze1()
        if self.current_maze == 2:  return self.maze2()
        if self.current_maze == 3:  return self.maze3()
        if self.current_maze == 4:  return self.maze4()
        if self.current_maze == 5:  return self.maze5()
        if self.current_maze == 6:  return self.maze6()
        if self.current_maze == 7:  return self.maze7()
        if self.current_maze == 8:  return self.maze8()
        if self.current_maze == 9:  return self.maze9()
        if self.current_maze == 10: return self.maze10()
        if self.current_maze == 11: return self.maze11()
        if self.current_maze == 12: return self.maze12()
        if self.current_maze == 13: return self.maze13()
        if self.current_maze > 13:
            print ('You Win! Press any key to play again')
            #interrupt = input()
            self.current_maze = 1
            return self.maze1()
            #print('You Win! No more mazes.')
            #pygame.quit()
            #sys.exit()

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
        self.mover = Mover()

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
        self.time_slow = True
        self.exit = False
        self.approval_mode = False

    def handle_input(self):

        is_there_input = False

        for event in pygame.event.get():
            if event.type == QUIT:
                return False, is_there_input
            else:
                if event.type != KEYDOWN:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()

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
                elif event.key == pygame.K_k:
                    view.show_controls = not view.show_controls
                elif event.key == pygame.K_v:
                    view.show_view = not view.show_view
                elif event.key == pygame.K_t:
                    self.time_slow = not self.time_slow
                elif event.key == pygame.K_x:
                    self.exit = True
                elif event.key == pygame.K_a:
                    self.approval_mode = not self.approval_mode

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
    ai_controlled = True
    approval_mode = False
    pygame.init()
    pygame.display.set_caption('Ai '+str(id(pygame)))
    controller = PyGameKeyboardController()
    controller.approval_mode = approval_mode
    if ai_controlled:
        controller.time_slow = False
    model = Model(controller, ai_controlled)
    if GAME_SHOW_SCREEN:
        view = PyGameView(model)

    logcount = len(os.listdir('./logs'))*10
    view.log = logcount
    sys.stdout = open('./logs/Console_Log'+str(logcount)+'.txt', 'w')

    # loop variable setup
    running = True
    # iterations = 0
    first_update = True

    # display the view initially
    if GAME_SHOW_SCREEN and view.show_view:
        view.draw()
        view.screen.blit(view.surface, (0,0))
        pygame.display.update()

    pygame.image.save(view.surface, 'screens/' + str(view.counter) + '_' + str(view.log) + '.jpg')

    while running:

        if os.path.getsize('./logs/Console_Log'+str(logcount)+'.txt') > 500000000:
            logcount += 1
            # if logcount == 101:
            #     raise Exception
            view.log = logcount
            sys.stdout = open('./logs/Console_Log' + str(logcount) + '.txt', 'w')

        # # output frame rate
        # iterations += 1
        # if time.time() - start_time > 1:
        #     start_time += 1
        #     print '%s fps' % iterations
        #     iterations = 0

        # listen for user input
        running, there_is_input = controller.handle_input()

        # if theres user input
        if model.ai_controlled or there_is_input or first_update:
            there_is_input, first_update = False, False
            # update the model
            if not controller.paused:
                model.update()

            # display the view
            if GAME_SHOW_SCREEN and view.show_view:
                view.draw()
                view.screen.blit(view.surface, (0,0))
                pygame.display.update()

            if not controller.paused:
                pygame.image.save(view.surface, 'screens/' + str(view.counter) + '_' + str(view.log) + '.jpg')


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

        if controller.time_slow:
            time.sleep(.1) # control frame rate (in seconds)
        if controller.exit:
            model.airis.error_stop = True
        if controller.approval_mode:
            pygame.display.set_caption('Ai ' + str(id(pygame)) + '- Plan Review Mode')
        else:
            pygame.display.set_caption('Ai ' + str(id(pygame)))

    pygame.quit()
    sys.exit()