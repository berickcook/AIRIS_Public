
############ PUZZLE GAME #################

GAME_SHOW_SCREEN = True
GAME_SCREEN_SIZE = (480, 360)

#MAP_SIZE = (640, 480) # original
GAME_MAP_SIZE = (480, 360) # GAME_MAP_SIZE is the number of pixels the entire game map is wide and tall
GAME_MAP_GRID = (20, 15) # GAME_MAP_GRID is the number of of tiles the game is wide and tall
GAME_MAP_START = (0, 0) # GAME_MAP_START is the coordinates on the screen where the top left of the game map is displayed
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