
############ PUZZLE GAME EDITOR #################

GAME_SHOW_SCREEN = True
GAME_SCREEN_SIZE = (640, 608)

#MAP_SIZE = (640, 480) # original
GAME_MAP_SIZE = (640, 480) # GAME_MAP_SIZE is the number of pixels the entire game map is wide and tall
GAME_MAP_GRID = (20, 15) # GAME_MAP_GRID is the number of of tiles the game is wide and tall
GAME_MAP_START = (0, 64) # GAME_MAP_START is the coordinates on the screen where the top left of the game map is displayed
GAME_POS_SIZE = (int(GAME_MAP_SIZE[0] / GAME_MAP_GRID[0]), int(GAME_MAP_SIZE[1] / GAME_MAP_GRID[1])) # pixel dim. of position