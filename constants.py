
############ PUZZLE GAME #################

GAME_SHOW_SCREEN = True
GAME_SCREEN_SIZE = (1000, 400)

#MAP_SIZE = (640, 480) # original
GAME_MAP_SIZE = (480, 360) # GAME_MAP_SIZE is the number of pixels the entire game map is wide and tall
GAME_MAP_GRID = (20, 15) # GAME_MAP_GRID is the number of of tiles the game is wide and tall
GAME_MAP_START = (5, 5) # GAME_MAP_START is the coordinates on the screen where the top left of the game map is displayed
GAME_POS_SIZE = (int(GAME_MAP_SIZE[0] / GAME_MAP_GRID[0]), int(GAME_MAP_SIZE[1] / GAME_MAP_GRID[1])) # pixel dim. of position

# these variables represent the same stuff as their GAME map conterparts
REP_MAP_SIZE = (480, 360)
REP_MAP_GRID = GAME_MAP_GRID
REP_MAP_START = (GAME_MAP_START[0]+GAME_MAP_SIZE[0]+5, GAME_MAP_START[1])
REP_POS_SIZE = (int(REP_MAP_SIZE[0] / REP_MAP_GRID[0]), int(REP_MAP_SIZE[1] / REP_MAP_GRID[1]))


PUZZLE_GAME_CONTROL_KEY = [
    "Keyboard Controls:",
    "    <space> = Pause/Play",
    "    v = Toggle view drawing",
    "    k = Toggle KeyBoard Control Key",
]
PUZZLE_GAME_CONTROL_KEY_START = (100, 100)



############ MNIST ########################

MNIST_SCREEN_SIZE = (600, 400)

MNIST_IMAGE_SIZE = (28*5, 28*5) # MNIST_IMAGE_SIZE is the dimensions (in pixels) that the mnist image will be rendered
MNIST_IMAGE_GRID = (28, 28) # MNIST_IMAGE_GRID is the pixel dimensions OF AN MNIST IMAGE
MNIST_IMAGE_START = (35, 35) # MNIST_IMAGE_START is the coordinates of where the mnist image will be displayed
MNIST_PIXEL_SIZE = (int(MNIST_IMAGE_SIZE[0] / MNIST_IMAGE_GRID[0]), int(MNIST_IMAGE_SIZE[1] / MNIST_IMAGE_GRID[1])) # pixel dim. of 1 mnist pixel


MNIST_CONTROL_KEY = [
    "Keyboard Controls:",
    "A          Toggle AIRIS Control",
    "space   AIRIS Pause/Play",
    "R          Render GUI",
]

MNIST_CONTROL_KEY_START = (MNIST_IMAGE_START[0], MNIST_IMAGE_START[1]+MNIST_IMAGE_SIZE[1]+55)

MNIST_TRAINING_ACCURACY_LOG = 'mnist_training_accuracy_log.txt'
MNIST_TESTING_ACCURACY_LOG  = 'mnist_testing_accuracy_log.txt'


########### OTHER ######################

# pretty printing constants
DEBUG_WITH_CONSOLE = False  # print AIRIS's thoughts to console
DEBUG_WITH_LOGFILE = True  # output AIRIS's thoughts to a file
DEBUG_LOGFILE_PATH = './debug_log.txt'
DEFAULT_INDENT = '|  '
DEFAULT_DRAW_LINE = False
