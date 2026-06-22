import pygame
import math

from regions import calculate_distances

YELLOW = (200, 200, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
RED = (255, 0, 0)

class Cell:
    def __init__(self, coords, terrain = 0, display = "", color = (255, 255, 255), aridity = float('inf'), nullevation = float('inf'), interiority = 0, island = False, gorge = False, depth = float('inf')):
        self.location = tuple(coords)
        self.terrain = terrain # 0 for empty, 1 for plain, 2 for water, 3 for mountain
        self.display = display
        self.color = tuple(color)
        self.aridity = aridity
        self.nullevation = nullevation
        self.interiority = interiority
        self.island = island
        self.gorge = gorge
        self.depth = depth # used to indicate how far from the map a void tile is

    def __repr__(self):
        return f"Cell({self.location}, terrain={self.terrain})"

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(self.location)
    
    def __eq__(self, other):
        return self.location == other.location
    
    def _to_json(self):
        return {
            'coords' : self.location,
            'terrain' : self.terrain,
            'display' : self.display,
            'color' : self.color
        }

def elevation(cell):
    if cell.aridity == float('inf'):
        return 0
    if cell.nullevation != 0:
        return 1000 * cell.aridity / (cell.aridity + cell.nullevation)
    else:
        return 1000 * cell.interiority

def realevation(cell):
    # THE FOLLOWING IS MORE PHYSICALLY ACCURATE BUT FUCKS UP THE COLORS
    if cell.nullevation != 0:
        if cell.aridity < cell.nullevation:
            return 1000 * cell.aridity / (cell.aridity + cell.nullevation)
        else:
            return 250 + 1000 * ((cell.aridity /  (cell.aridity + cell.nullevation)) ^ 2)
    else:
        return 1000 * (2 ^ (cell.interiority - 1))

def get_background(cell, view = 0):
    if cell.terrain == 0:
        r = 0
        g = 0
        b = max(100 / (cell.depth + 1), 20)
    if view == 0:
        if cell.terrain == 1:
            try:
                r = min(max(int(elevation(cell) * 3 / 50), (cell.aridity - 1)* 7), 80)
            except:
                r = 0
            g = 40
            b = 0
        if cell.terrain == 2:
            r = 0
            g = 40
            b = 0
        if cell.terrain == 3:
            r = 60
            g = min(60, 40 + (cell.interiority - 1) * 10)
            b = min(60, 40 + (cell.interiority - 1) * 20)
    if view == 1 and cell.terrain != 0:
        r = min(255 * elevation(cell) / 3000, 255)
        g = 0
        b = int((255 - r)/10)
    if view == 2 and cell.terrain !=0:
        try:
            r = min(int(cell.aridity * 7), 255)
        except:
            r = 0
        g = r
        b = max(180 - r, 0)
    if view == 3 and cell.terrain !=0:
        (r, g, b) = int(cell.color[0]/2), int(cell.color[1]/2), int(cell.color[2]/2)
    return (r,g,b)

def draw_minimap(grid, x, y, mini_cell_size = 3):

    GRID_WIDTH = len(grid[0])
    GRID_HEIGHT = len(grid)

    screen = pygame.display.get_surface()

    calculate_distances(grid)
    radius = max(mini_cell_size * GRID_WIDTH, mini_cell_size * GRID_HEIGHT)
    pygame.draw.rect(screen, BLACK, (x, y, mini_cell_size * GRID_WIDTH, mini_cell_size * GRID_HEIGHT))
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            if grid[row][col]:
                xx = x + col * mini_cell_size
                yy = y + row * mini_cell_size
                
                (r, g, b) = get_background(grid[row][col])
                if grid[row][col].terrain == 2: (r,g,b) = (0,0,80)
                r = (1.5 * r)
                g = (1.5 * g)
                b = (1.5 * b)
                pygame.draw.rect(screen, (r, g, b), (xx, yy, mini_cell_size, mini_cell_size))
    pygame.draw.rect(screen, YELLOW, (x, y, mini_cell_size * GRID_WIDTH, mini_cell_size * GRID_HEIGHT), 3, border_radius = 5)
