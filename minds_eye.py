from minds_eye_constants import *
from minds_eye_game_objects import *
import sys, os, glob
import ast

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

    def draw(self):

        # commented out because we're only updating squares if they change
        # # fill background
        # self.surface.fill(pygame.Color('black'))

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

        # maze game setup
        self.object_list = []
        self.make_singletons()
        self.game_map = self.floor_init()
        print('object list', self.object_list[0])
        # self.maze()

    def make_singletons(self):

        self.floor = Floor()
        self.object_list.append(self.floor)
        self.character    = Character()
        self.object_list.append(self.character)
        self.wall         = Wall()
        self.object_list.append(self.wall)
        self.battery = Battery()
        self.object_list.append(self.battery)
        self.door = Door()
        self.object_list.append(self.door)
        self.key = Key()
        self.object_list.append(self.key)
        self.extinguisher = Extinguisher()
        self.object_list.append(self.extinguisher)
        self.fire         = Fire()
        self.object_list.append(self.fire)
        self.right_arrow = RightArrow()
        self.object_list.append(self.right_arrow)
        self.left_arrow = LeftArrow()
        self.object_list.append(self.left_arrow)
        self.down_arrow = DownArrow()
        self.object_list.append(self.down_arrow)
        self.up_arrow = UpArrow()
        self.object_list.append(self.up_arrow)
        self.open_door   = OpenDoor()
        self.object_list.append(self.open_door)
        self.character_on_right_arrow = CharacterOnRightArrow()
        self.object_list.append(self.character_on_right_arrow)
        self.character_on_left_arrow  = CharacterOnLeftArrow()
        self.object_list.append(self.character_on_left_arrow)
        self.character_on_down_arrow  = CharacterOnDownArrow()
        self.object_list.append(self.character_on_down_arrow)
        self.character_on_up_arrow    = CharacterOnUpArrow()
        self.object_list.append(self.character_on_up_arrow)
        self.character_on_open_door   = CharacterOnOpenDoor()
        self.object_list.append(self.character_on_open_door)
        self.mover = Mover()
        self.object_list.append(self.mover)

    def floor_init(self):
        # initialize everything to a floor tile
        game_map = []
        for x in range(GAME_MAP_GRID[0]):
            game_map.append([])
            for y in range(GAME_MAP_GRID[1]):
                game_map[x].append(self.floor)
        return game_map

    def update(self, screen):
        game_map = self.floor_init()
        for x in range(GAME_MAP_GRID[0]):
            for y in range(GAME_MAP_GRID[1]):
                game_map[x][y] = self.object_list[int(screen[x][y])]

        self.game_map = game_map

class PyGameKeyboardController(object):
    '''
        Keyboard controller that responds to keyboard input
    '''

    def __init__(self):

        self.paused = False
        self.player_input = 'nothing'
        self.time_slow = True
        self.exit = False
        self.mode = False

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
                elif event.key == pygame.K_m:
                    self.mode = not self.mode
                    is_there_input = True

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
    pygame.display.set_caption('AI Mind\'s Eye')
    controller = PyGameKeyboardController()
    model = Model(controller)
    view = PyGameView(model)
    view_mode = False
    log_current = 0
    log_len = 0

    # loop variable setup
    running = True

    # display the view initially
    if GAME_SHOW_SCREEN and view.show_view:
        view.draw()
        view.screen.blit(view.surface, (0,0))
        pygame.display.update()

    plan_log = []

    while running:

        # listen for user input
        running, there_is_input = controller.handle_input()

        if not len(plan_log):
            try:
                if not controller.mode:
                    LatestFile = max(glob.iglob('./plan_log/*.txt'), key=os.path.getctime)
                    view_mode = False
                else:
                    LatestFile = max(glob.iglob('./predict_log/*.txt'), key=os.path.getctime)
                    view_mode = True

                text_file = open(LatestFile, "r")
                while True:
                    line = text_file.readline()
                    if line:
                        plan_log.append(line)
                    else:
                        break
                text_file.close()
                log_len = len(plan_log)
                log_current = 1
            except ValueError:
                pass
        else:

            if not view_mode:
                screen = ast.literal_eval(plan_log.pop())
            else:
                screen = ast.literal_eval(plan_log.pop(0))
            model.update(screen)

            # display the view
            if GAME_SHOW_SCREEN and view.show_view:
                view.draw()
                view.screen.blit(view.surface, (0, 0))
                pygame.display.update()

            if not view_mode:
                pygame.display.set_caption('AI Mind\'s Eye - Current Plan - Step ' + str(log_current) + ' of ' + str(log_len))
            else:
                pygame.display.set_caption('AI Mind\'s Eye - Predicted States - State ' + str(log_current) + ' of ' + str(log_len))

            log_current += 1

        if there_is_input:
            plan_log = []

    pygame.quit()
    sys.exit()