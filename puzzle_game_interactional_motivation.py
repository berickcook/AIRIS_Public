import pygame
import time, sys, csv
from pygame.locals import QUIT, KEYDOWN
from game_objects import *
from constants import GAME_MAP_GRID, GAME_MAP_START, GAME_SHOW_SCREEN, GAME_SCREEN_SIZE, REP_MAP_GRID, BATTERY, WALL, \
    PUZZLE_GAME_CONTROL_KEY, PUZZLE_GAME_CONTROL_KEY_START, MAX_SMELL, FORWARD, SNIFF_LEFT, SNIFF_FRONT, SNIFF_RIGHT, \
    DECREASE, INCREASE, STABLE, BUMP, EAT, TURN_LEFT, TURN_RIGHT, ACTIONS_IMOSM_AIRIS
from other_useful_functions import pprint
import datetime
import numpy as np
from game_objects_color import BumpSprite, FeelEmptySprite, FeelWallSprite
import networkx as nx
import structlog
from imosm import Interaction, Agent
import tracer

# Directions
UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3
DIRECTIONS = np.array([[0, -1], [-1, 0], [0, 1], [1, 0]])


class PyGameView(object):
    '''
        PyGameView controls the display
    '''

    def __init__(self, model):

        self.model = model
        self.screen = pygame.display.set_mode(GAME_SCREEN_SIZE)  # a pygame screen
        self.surface = pygame.Surface(GAME_SCREEN_SIZE)  # a pygame surface is the thing you draw on

        self.show_view = True  # toggle display
        self.show_controls = False  # toggle control display

        self.counter_font = pygame.font.SysFont("courier", 20, bold=True)

    def draw(self):

        # commented out because we're only updating squares if they change
        # # fill background
        # self.surface.fill(pygame.Color('black'))

        self.draw_game_map()

        self.draw_representation_map()

        # draw control key
        if self.show_controls:
            for n, line in enumerate(PUZZLE_GAME_CONTROL_KEY):
                self.draw_text(line, PUZZLE_GAME_CONTROL_KEY_START[0],
                               PUZZLE_GAME_CONTROL_KEY_START[1]+14*n, 20)

        # Draw counter
        counter_surface = self.counter_font.render(f'{model.time_counter:04}', True, (255, 255, 255))
        counter_rectangle = counter_surface.get_rect(topleft=(920, 6))
        self.surface.fill((64, 64, 64), counter_rectangle)
        self.surface.blit(counter_surface, counter_rectangle)

        # update display
        pygame.display.update()

    def draw_game_map(self):

        # variable setup
        w, h = GAME_MAP_GRID  # number of positions wide and high
        ms = GAME_MAP_START

        # draw each position in the grid
        for x in range(w):
            for y in range(h):
                if self.model.change_in_game_map[x][y]:
                    if isinstance(self.model.game_map[x][y], Character):
                        self.model.game_map[x][y].draw_game_image(self, x, y, 90 * self.model.direction)
                    else:
                        self.model.game_map[x][y].draw_game_image(self, x, y)

    def draw_representation_map(self):

        # variable setup
        w, h = REP_MAP_GRID  # number of positions wide and high
        ms = REP_MAP_START

        # Redraw the changed representations
        for key, sprite in self.model.changes_in_rep.items():
            sprite.draw_representation_image(self, key[0], key[1])
            # Prepare for next update
            if isinstance(sprite, BumpSprite) or isinstance(sprite, FeelWallSprite):
                self.model.changes_in_rep[(key[0], key[1])] = self.model.wall
            if isinstance(sprite, FeelEmptySprite):
                self.model.changes_in_rep[(key[0], key[1])] = self.model.floor
                smell_color = mcolors.to_hex(self.model.smell_color_map(self.model.smell_grid[key[0]][key[1]] / self.model.max_smell))
                self.model.changes_in_rep[(key[0], key[1])].set_smell(smell_color)
            if isinstance(sprite, Wall) or isinstance(sprite, Floor):
                self.model.changes_in_rep[(key[0], key[1])] = None
        self.model.changes_in_rep = {k: v for k, v in self.model.changes_in_rep.items() if v is not None}

        # draw each position in the grid
        for x in range(w):
            for y in range(h):
                if self.model.change_in_game_map[x][y]:
                    smell_color = mcolors.to_hex(self.model.smell_color_map(self.model.smell_grid[x][y]/self.model.max_smell))
                    self.model.game_map[x][y].set_smell(smell_color)
                    if isinstance(self.model.game_map[x][y], Character):
                        self.model.game_map[x][y].draw_representation_image(self, x, y, 90 * self.model.direction)
                    else:
                        self.model.game_map[x][y].draw_representation_image(self, x, y)

    def draw_text(self, text, x, y, size, color=(100, 100, 100)):
        basicfont = pygame.font.SysFont(None, size)
        text_render = basicfont.render(text, True, color)
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
        self.show = True  # show current model
        self.controller = controller

        # Egocentric smell setup
        self.character_current_pos = np.array([0, 0])
        self.direction = UP
        self.previous_smell = 0
        self.outcome = STABLE
        self.changes_in_rep = {}

        self.env_grid = np.zeros((GAME_MAP_GRID[0], GAME_MAP_GRID[1]), dtype=int)
        self.character_current_floor = None
        self.change_in_game_map = np.full((GAME_MAP_GRID[0], GAME_MAP_GRID[1]), False, dtype=bool)
        self.smell_grid = np.full(self.env_grid.shape, MAX_SMELL)
        self.smell_graph = None
        self.smell_color_map = mcolors.LinearSegmentedColormap.from_list("custom_gradient", ["#00ff00", "white"])
        self.max_smell = MAX_SMELL

        # maze game setup
        self.make_singletons()
        self.current_maze = 0
        self.get_next_maze()

        # AGI setup
        self.screen_input = []
        for x in range(GAME_MAP_GRID[0]):
            self.screen_input.append([])
            for y in range(GAME_MAP_GRID[1]):
                self.screen_input[x].append(0.0)
        self.aux_input = [self.keys_collected, self.extinguishers_collected]
        self.action_space = ['up', 'down', 'left', 'right', 'nothing', 'forward', 'turn_left', 'turn_right']
        self.ai_controlled = ai_controlled
        self.time_counter = 0

        # IMOSC setup
        self.imosm = None
        # The tracer
        self.tracer = structlog.get_logger()
        self.player_action = ''

    # This function updates the model
    def update(self):

        pprint('-------------------------------------------- TIME STEP %d --------------------------------------------'
            % self.time_counter, new_line_start=True, draw_line=False)

        # Save the screenshot before incrementing time counter
        pygame.image.save(view.screen, f"logs/{self.time_counter:04}.png")
        # Save the trace of the previous interaction
        trace_dict = {"step": self.time_counter, "action": self.player_action}

        self.time_counter += 1

        self.change_in_game_map[:, :] = False

        self.player_action = 'nothing'

        # get user input
        if not self.ai_controlled:
            self.player_action = self.get_action()

        # set environment values to current and output to ai
        self.current_environment()

        if self.ai_controlled:
            '''
            
            Send current self.screen_input and self.aux_input to your ai
            and return the action ('up', 'down', 'left', 'right', 'nothing') to be taken
            
            EXAMPLE:
            
            player_action = ai.capture_current_environment(self.screen_input, self.aux_input)
            
            '''
            self.player_action = ACTIONS_IMOSM_AIRIS[self.imosm.action(self.outcome)]

        pprint('ACTION:\t%s' % self.player_action, new_line_start=True, draw_line=False)

        # update the game according to the player's input
        self.outcome = self.game_logic(self.player_action)
        # print(f"OUTCOME:\t{self.outcome}")

        # go to next level if player beats the current level
        if self.batteries_collected == self.num_batteries:
            self.get_next_maze()

        # reset the maze if the character dies
        if self.maze_reset:
            self.get_next_maze()

        # output post-action environment to ai
        self.current_environment()

        # Log the trace of this interaction
        self.tracer = self.tracer.bind(**trace_dict)
        self.tracer.info("", **self.imosm.trace_record)
        self.tracer = self.tracer.new()

        '''
        Send the new self.screen_input and self.aux_input to your ai so that it can see what changed.
        No return value necessary.
        
        EXAMPLE:
        
        ai.capture_post_environment(self.screen_input, self.aux_input)
        '''

    def get_action(self):
        return self.controller.player_input

    def current_environment(self):

        for x in range(GAME_MAP_GRID[0]):
            for y in range(GAME_MAP_GRID[1]):
                self.screen_input[x][y] = self.game_map[x][y].id

        self.aux_input[0] = self.keys_collected
        self.aux_input[1] = self.extinguishers_collected

    # These functions control game logic
    def game_logic(self, player_input):

        outcome = STABLE
        front_position = self.character_current_pos + DIRECTIONS[self.direction]
        left_position = self.character_current_pos + DIRECTIONS[(self.direction + 1) % 4]
        right_position = self.character_current_pos + DIRECTIONS[self.direction - 1]
        position_smell = self.smell_grid[tuple(self.character_current_pos)]
        front_smell = self.smell_grid[tuple(front_position)]
        left_smell = self.smell_grid[tuple(left_position)]
        right_smell = self.smell_grid[tuple(right_position)]

        if player_input != 'nothing':
            character_new_pos = self.character_current_pos.copy()
            feel_pos = self.character_current_pos.copy()
            if player_input == 'up':
                character_new_pos += np.array([0, -1])
            if player_input == 'down':
                character_new_pos += np.array([0, 1])
            if player_input == 'left':
                character_new_pos += np.array([-1, 0])
            if player_input == 'right':
                character_new_pos += np.array([1, 0])
            if player_input == 'forward':
                character_new_pos += DIRECTIONS[self.direction]
                new_front_pos = character_new_pos + DIRECTIONS[self.direction]
                if new_front_pos[0] < 0 or new_front_pos[0] >= GAME_MAP_GRID[0] or new_front_pos[1] < 0 or new_front_pos[1] >= GAME_MAP_GRID[1]:
                    new_front_smell = 0
                else:
                    new_front_smell = self.smell_grid[tuple(character_new_pos + DIRECTIONS[self.direction])]
                outcome = STABLE + (new_front_smell < front_smell) - (new_front_smell > front_smell)
            if player_input == "turn_left":
                outcome = STABLE + (left_smell < front_smell) - (left_smell > front_smell)
                self.direction = (self.direction + 1) % 4
            if player_input == "turn_right":
                outcome = STABLE + (right_smell < front_smell) - (right_smell > front_smell)
                self.direction = (self.direction + 3) % 4
            if player_input == 'sniff_left':
                feel_pos += DIRECTIONS[(self.direction + 1) % 4]
            if player_input == 'sniff_front':
                feel_pos += DIRECTIONS[self.direction]
            if player_input == 'sniff_right':
                feel_pos += DIRECTIONS[(self.direction - 1) % 4]

            # Display the feel interaction in the representation
            if not np.array_equal(feel_pos, self.character_current_pos):
                if self.env_grid[tuple(feel_pos)] == 2:  # WALL
                    self.changes_in_rep[tuple(feel_pos)] = self.feel_wall_sprite
                    feel_smell = self.smell_grid[tuple(feel_pos)]
                    # outcome = STABLE + (feel_smell < position_smell) - (feel_smell > position_smell)
                    return BUMP  # Don't smell
                else:
                    self.changes_in_rep[tuple(feel_pos)] = self.feel_empty_sprite
                    feel_smell = self.smell_grid[tuple(feel_pos)]
                    return STABLE + (feel_smell < position_smell) - (feel_smell > position_smell)

            new_tile = self.game_map[character_new_pos[0]][character_new_pos[1]]
            if isinstance(new_tile, Floor):
                self.move_character(new_tile, character_new_pos, self.character)

            # Redraw the character for the case it turned in place
            elif isinstance(new_tile, Character):
                self.change_in_game_map[tuple(self.character_current_pos)] = True

            # Return the BUMP outcome
            elif isinstance(new_tile, Wall):
                self.changes_in_rep[tuple(character_new_pos)] = self.bump_sprite
                outcome = BUMP

            elif isinstance(new_tile, Battery):
                self.move_character(new_tile, character_new_pos, self.character)
                self.collect_battery(character_new_pos)
                self.set_smell_grid()
                outcome = EAT

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

        return outcome

    def move_character(self, new_tile, character_new_pos, character_and_floor):

        character_old_floor = self.character_current_floor
        character_old_pos = np.array(self.character_current_pos)

        if character_and_floor != self.character_on_open_door:
            self.character_current_floor = new_tile
        else:
            self.character_current_floor = self.open_door

        self.character_current_pos[:] = character_new_pos
        self.game_map[self.character_current_pos[0]][self.character_current_pos[1]] = character_and_floor
        self.change_in_game_map[self.character_current_pos[0]][self.character_current_pos[1]] = True
        self.game_map[character_old_pos[0]][character_old_pos[1]] = character_old_floor
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

        with open('custom_levels/' + str(self.current_maze) + '.csv', 'r') as File:
            read = csv.reader(File, delimiter=',')
            for r, row in enumerate(read):
                row[0] = int(row[0])
                row[1] = int(row[1])
                row[2] = int(row[2])

                if r == 0:
                    self.character_start_pos = (row[0], row[1])
                    self.character_current_pos[:] = ([row[0], row[1]])
                    self.character_current_floor = self.floor
                    self.num_batteries = row[2]
                else:
                    # Initialize the grid
                    self.env_grid[row[0]][row[1]] = row[2]
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

        # Refresh all tiles to be redrawn
        self.env_grid[:, :] = 0
        self.direction = UP
        self.change_in_game_map[:, :] = True

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

        # The smell graph
        self.smell_graph = nx.Graph()
        for r in range(self.env_grid.shape[0]):
            for c in range(self.env_grid.shape[1]):
                if self.env_grid[r, c] == WALL:
                    continue  # skip walls
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.env_grid.shape[0] and 0 <= nc < self.env_grid.shape[1] and \
                            self.env_grid[nr, nc] != WALL:
                        self.smell_graph.add_edge((r, c), (nr, nc), weight=1)
        self.set_smell_grid()

        self.batteries_collected = 0
        self.extinguishers_collected = 0
        self.keys_collected = 0
        self.maze_reset = False

    def set_smell_grid(self):
        """Set the smell grid. Called when the maze is loaded or when a target is eaten"""
        # --- Identify target cells ---
        targets = [(r, c) for r in range(self.env_grid.shape[0]) for c in range(self.env_grid.shape[1])
                   if self.game_map[r][c].id == BATTERY]
        # --- Compute shortest distances from each cell to the nearest target ---
        self.smell_grid[:, :] = MAX_SMELL
        for target in targets:
            lengths = nx.single_source_dijkstra_path_length(self.smell_graph, target)
            for (r, c), dist in lengths.items():
                self.smell_grid[r, c] = min(self.smell_grid[r, c], dist)
        print(self.smell_grid)
        if len(targets) > 0:
            self.max_smell = self.smell_grid[self.smell_grid != MAX_SMELL].max()
        # Redraw entire map to show updated smell values
        self.change_in_game_map[:, :] = True

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
        self.bump_sprite = BumpSprite()
        self.feel_empty_sprite = FeelEmptySprite()
        self.feel_wall_sprite = FeelWallSprite()


class PyGameKeyboardController(object):
    '''
        Keyboard controller that responds to keyboard input
    '''

    def __init__(self):

        self.paused = False
        self.player_input = 'nothing'

    def handle_input(self):

        is_there_input = False

        for event in pygame.event.get():
            if event.type == QUIT:
                return False, is_there_input
            else:
                if event.type != KEYDOWN:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()

                        # print('mouse position = (%d,%d)') % (mouse_pos[0], mouse_pos[1])

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
        if keys[pygame.K_KP8] or keys[pygame.K_8]:
            is_there_input = True
            self.player_input = 'forward'
            number_of_keys_pressed += 1
        if keys[pygame.K_KP4] or keys[pygame.K_4]:
            is_there_input = True
            self.player_input = 'turn_left'
            number_of_keys_pressed += 1
        if keys[pygame.K_KP6] or keys[pygame.K_6]:
            is_there_input = True
            self.player_input = 'turn_right'
            number_of_keys_pressed += 1
        if keys[pygame.K_KP1]:
            is_there_input = True
            self.player_input = 'sniff_left'
            number_of_keys_pressed += 1
        if keys[pygame.K_KP2]:
            is_there_input = True
            self.player_input = 'sniff_front'
            number_of_keys_pressed += 1
        if keys[pygame.K_KP3]:
            is_there_input = True
            self.player_input = 'sniff_right'
            number_of_keys_pressed += 1

        if number_of_keys_pressed > 0:
            print(self.player_input)
        if number_of_keys_pressed > 1:
            print(self.player_input, '>1')
            self.player_input = original_player_input
        elif number_of_keys_pressed == 0:
            self.player_input = 'nothing'

        return True, is_there_input


if __name__ == '__main__':

    # pygame setup
    ai_controlled = False
    if sys.argv.__len__() > 1:
        if sys.argv[1] == 'imo':
            ai_controlled = True
    pygame.init()
    pygame.display.set_caption('Ai '+str(id(pygame)))
    print(f'\33]0;{id(pygame)}\a', end='', flush=True)
    controller = PyGameKeyboardController()
    model = Model(controller, ai_controlled)
    if GAME_SHOW_SCREEN:
        view = PyGameView(model)

    # loop variable setup
    running = True
    # iterations = 0
    first_update = True

    # display the view initially
    if GAME_SHOW_SCREEN and view.show_view:
        view.draw()
        view.screen.blit(view.surface, (0, 0))
        pygame.display.update()

    # Initialize the agent
    interactions = [
        Interaction(FORWARD, STABLE, -10),
        Interaction(FORWARD, BUMP, -10),
        Interaction(FORWARD, INCREASE, 10),
        Interaction(FORWARD, DECREASE, -10),
        Interaction(FORWARD, EAT, 10),
        Interaction(TURN_LEFT, STABLE, -5),
        Interaction(TURN_LEFT, INCREASE, 5),
        Interaction(TURN_LEFT, DECREASE, -10),
        Interaction(TURN_LEFT, EAT, 10),
        Interaction(TURN_RIGHT, STABLE, -5),
        Interaction(TURN_RIGHT, INCREASE, 5),
        Interaction(TURN_RIGHT, DECREASE, -10),
        Interaction(TURN_RIGHT, EAT, 10),
    ]
    interactions = [
        Interaction(FORWARD, STABLE, 5),
        Interaction(FORWARD, BUMP, -10),
        Interaction(TURN_LEFT, STABLE, -3),
        Interaction(TURN_LEFT, BUMP, -3),
        Interaction(TURN_RIGHT, STABLE, -3),
        Interaction(TURN_RIGHT, BUMP, -3),
        Interaction(SNIFF_FRONT, STABLE, -1),
        Interaction(SNIFF_FRONT, BUMP, -1),
        Interaction(SNIFF_LEFT, STABLE, -1),
        Interaction(SNIFF_LEFT, BUMP, -1),
        Interaction(SNIFF_RIGHT, STABLE, -1),
        Interaction(SNIFF_RIGHT, BUMP, -1),

        Interaction(SNIFF_FRONT, DECREASE, -1),
        Interaction(SNIFF_FRONT, INCREASE, -1),
        Interaction(SNIFF_LEFT, DECREASE, -1),
        Interaction(SNIFF_LEFT, INCREASE, -1),
        Interaction(SNIFF_RIGHT, DECREASE, -1),
        Interaction(SNIFF_RIGHT, INCREASE, -1),
        Interaction(FORWARD, INCREASE, 10),
        Interaction(FORWARD, DECREASE, -1),
        Interaction(FORWARD, EAT, 5),
        Interaction(TURN_LEFT, INCREASE, -1),
        Interaction(TURN_LEFT, DECREASE, -5),
        Interaction(TURN_LEFT, EAT, 1),
        Interaction(TURN_RIGHT, INCREASE, -1),
        Interaction(TURN_RIGHT, DECREASE, -5),
        Interaction(TURN_RIGHT, EAT, 1),
    ]
    model.imosm = Agent(interactions)

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
        if model.ai_controlled or there_is_input or first_update:
            there_is_input, first_update = False, False
            # update the model
            if not controller.paused:
                model.update()

            # display the view
            if GAME_SHOW_SCREEN and view.show_view:
                view.draw()
                view.screen.blit(view.surface, (0, 0))
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

        time.sleep(0.10)  # control frame rate (in seconds)

    pygame.quit()
    sys.exit()
