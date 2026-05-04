import random
import numpy as np
from config import CHUNK_WIDTH_TILES, CHUNK_HEIGHT_TILES

"""

generates a random binary grid and uses cellular automata rules to produce cave-like tile layouts.returns a numpy array of SOLID/EMPTY(1/0) integers ready to be used in a Chunk.

"""

# How big the grid is...changed it so it imports from config
GRID_WIDTH = CHUNK_WIDTH_TILES
GRID_HEIGHT = CHUNK_HEIGHT_TILES

# Parameters for cellular automata
CHANCE_TO_START_ALIVE = 0.55 #keep it at .6 for a playable level for noe makig it .45  or .5 gives a more 'interesting' level but that needs A* solvability validation just bfs does not gaurentee player solvability
DEATH_LIMIT = 4
BIRTH_LIMIT = 5
NUMBER_OF_STEPS = 4

def create_grid(width, height):
    """ Create a two-dimensional grid of specified size. """
    return np.zeros((height, width), dtype=np.int8)

def initialize_grid(grid):
    """ Randomly set grid locations to on/off based on chance. """
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for column in range(width):
            if random.random() <= CHANCE_TO_START_ALIVE:
                grid[row][column] = 1

def count_alive_neighbors(grid, x, y):
    """ Count neighbors that are alive. """
    height = len(grid)
    width = len(grid[0])
    alive_count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            neighbor_x = x + i
            neighbor_y = y + j
            if i == 0 and j == 0:
                continue
            elif neighbor_x < 0 or neighbor_y < 0 or neighbor_y >= height or neighbor_x >= width:
                # Edges are considered alive. Makes map more likely to appear naturally closed.
                alive_count += 1
            elif grid[neighbor_y][neighbor_x] == 1:
                alive_count += 1
    return alive_count

def do_simulation_step(old_grid):
    """ Run a step of the cellular automaton. """
    height = len(old_grid)
    width = len(old_grid[0])
    new_grid = create_grid(width, height)
    for x in range(width):
        for y in range(height):
            alive_neighbors = count_alive_neighbors(old_grid, x, y)
            if old_grid[y][x] == 1:
                if alive_neighbors < DEATH_LIMIT:
                    new_grid[y][x] = 0
                else:
                    new_grid[y][x] = 1
            else:
                if alive_neighbors > BIRTH_LIMIT:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = 0
    return new_grid

def get_raw_tile_array():
    grid = create_grid(GRID_WIDTH, GRID_HEIGHT)
    initialize_grid(grid)
    for step in range(NUMBER_OF_STEPS):
        grid = do_simulation_step(grid)
    with np.printoptions(threshold=np.inf,linewidth=np.inf):
        print(grid)
    return grid

if __name__ == "__main__":
    get_raw_tile_array()