import pygame
from regions import calculate_distances
from map import Cell
from math import ceil

CELL_SIZE = 18
FONT_SIZE = 18
PREV_FONT_SIZE = 36
TILE_SIZE = 3

font = pygame.font.SysFont('monospace', FONT_SIZE)
preview_font = pygame.font.SysFont('monospace', PREV_FONT_SIZE)

WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARKRED = (120, 0, 0)
YELLOW = (200, 200, 0)
BLUE = (0, 180, 255)
GREEN = (0, 200, 0)
DARKGREEN = (0, 120, 0)
BROWN = (200, 255, 0)

def set_display():

    screen_info = pygame.display.Info()
    screen_width, screen_height = screen_info.current_w, screen_info.current_h
    print(f"Setting resolution to {screen_width}x{screen_height}")
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.toggle_fullscreen()
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Cartominoes")
    return screen

def draw_text(screen, text, x, y, font = preview_font, color = WHITE):

    text = str(text)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_preview_tile(screen, tile, colors, x, y, active = False):
    pygame.draw.rect(screen, BLACK, (x,y, PREV_FONT_SIZE * 3, PREV_FONT_SIZE * 3))
    for row in range(TILE_SIZE):
        for col in range(TILE_SIZE):
            char = tile[row][col]
            color = colors[row][col]
            text_surface = preview_font.render(char, True, color)
            screen.blit(text_surface, (3 + x + col * PREV_FONT_SIZE,y + row * PREV_FONT_SIZE))
    pygame.draw.rect(screen, DARKGREEN, (x - 3,y - 3, 6 + PREV_FONT_SIZE * 3, 6 + PREV_FONT_SIZE * 3), 5, border_radius = 3)
    if active:
        pygame.draw.rect(screen, GREEN, (x,y, PREV_FONT_SIZE * 3, PREV_FONT_SIZE * 3), 2, border_radius = 3)
    else:
        pygame.draw.rect(screen, BLACK, (x,y, PREV_FONT_SIZE * 3, PREV_FONT_SIZE * 3), 2, border_radius = 3)

def draw_curtile(screen, grid, x, y, selrow, selcol, curtile, curcolors, show = False, can_place_tile = True):

    screen_width, screen_height = screen.get_size()

    def draw_cell(cell, x, y):

        if x > screen_width or y > screen_height or x + CELL_SIZE < 0 or y + CELL_SIZE < 0:
            return
        
        text = ""
        color = cell.color
        if cell.display == "═" or cell.display == "█":
            text = cell.display * 2
            x -= (FONT_SIZE * 11/ 36)
        else:
            text = cell.display
        pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE))
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x + 3, y))

    if grid[selrow][selcol].display == "":
        for i in range(3):
            for j in range(3):
                if can_place_tile:
                    cell, color = curtile[i][j], curcolors[i][j]
                else:
                    cell, color = curtile[i][j], RED
                if not show: 
                    color = tuple(n/2 for n in color)
                draw_cell(Cell((0,0), display = cell, color = color),
                    (screen_width / 2) - CELL_SIZE * 1.5 + CELL_SIZE * j, (screen_height / 2) - CELL_SIZE * 1.5 + CELL_SIZE * i)
                
def draw_biome(screen, grid, x, y, highlight_cell, view = 0, biomes = []):

    grid_width, grid_height = len(grid[0]), len(grid)
    screen_width, screen_height = screen.get_size()


    def draw_cell(cell, x, y):

        if x > screen_width or y > screen_height or x + CELL_SIZE < 0 or y + CELL_SIZE < 0:
            return
        
        def get_random_flower(n):
            selections = [(251, 178, 109), (245, 125, 98), (225, 91, 100), (152, 88, 192)]
            return selections[n]
        
        text = ""
        color = cell.color
        if cell.display == "═" or cell.display == "█":
            text = cell.display * 2
            x -= (FONT_SIZE * 11/ 36)
        else:
            text = cell.display
        (r, g, b) = get_background(cell, view)
        r = min(int(r * 1.5), 255)
        g = min(int(g * 1.5), 255)
        b = min(int(b * 1.5), 255)
        color = (min(255,int(color[0] * 1.5)), min(255,int(color[1] * 1.5)), min(255,int(color[2] * 1.5)))
        if cell.display == "✿":
            color = get_random_flower(hash(cell) % 3)
 
        pygame.draw.rect(screen, (r, g, b), (x, y, CELL_SIZE, CELL_SIZE))
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x + 3, y))

    biome_list = [biome for biome in biomes if grid[highlight_cell[0]][highlight_cell[1]] in biome.cells]
    for biome in biome_list:
        for cell in biome.cells:
            row, col = cell.location[1], cell.location[0]
            draw_cell(grid[row][col], x + 3 + col * CELL_SIZE, y + 3 + row * CELL_SIZE)

def draw_grid(
    grid, clouds, x, y, highlight_cell = False, 
    selrow = 0, selcol = 0, 
    curtile = None, curcolors = None, 
    biomes = [], view = 0, show = False, draw_all = False,
    render_surface = None
):

    grid_width = len(grid[0])
    grid_height = len(grid)

    def draw_cell(cell, x, y):

        if not draw_all and (x > screen_width or y > screen_height or x + CELL_SIZE < 0 or y + CELL_SIZE < 0):
            return
        
        def get_random_flower(n):
            selections = [(251, 178, 109), (245, 125, 98), (225, 91, 100), (152, 88, 192)]
            return selections[n]
        
        text = ""
        color = cell.color
        if cell.display == "═" or cell.display == "█":
            text = cell.display * 2
            x -= (FONT_SIZE * 11/ 36)
        else:
            text = cell.display
        if cell.display == "." and cell.location != (0, 0): #(0,0) means it's the tile you're placing
            text = ""
        (r, g, b) = get_background(cell, view)
        if cell.display == "✿":
            color = get_random_flower(hash(cell) % 3)
        if highlight_cell:           
            for biome in biome_list:
                if cell in biome.cells:
                    r = min(int(r * 1.5), 255)
                    g = min(int(g * 1.5), 255)
                    b = min(int(b * 1.5), 255)
                    color = (min(255,int(color[0] * 1.5)), min(255,int(color[1] * 1.5)), min(255,int(color[2] * 1.5)))
        r = min(255, r + clouds[row][col])
        g = min(255, g + clouds[row][col])
        b = min(255, b + clouds[row][col])
        pygame.draw.rect(render_surface, (r, g, b), (x, y, CELL_SIZE, CELL_SIZE))   
        text_surface = font.render(text, True, color)
        render_surface.blit(text_surface, (x + 3, y))
        # cloudtext = font.render(str(clouds[row][col]), True, WHITE)
        # render_surface.blit(cloudtext, (x + 3, y))

    
    for row in range(grid_height):
        for col in range(grid_width):
            if grid[row][col]:
                draw_cell(grid[row][col], x + 3 + col * CELL_SIZE, y + 3 + row * CELL_SIZE)

def get_background(cell, view = 0):
    def elevation(cell):
        if cell.aridity == float('inf'):
            return 0
        if cell.nullevation != 0:
            return 1000 * cell.aridity / (cell.aridity + cell.nullevation)
        else:
            return 1000 * cell.interiority
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

    grid_width = len(grid[0])
    grid_height = len(grid)

    screen = pygame.display.get_surface()

    calculate_distances(grid)
    radius = max(mini_cell_size * grid_width, mini_cell_size * grid_height)
    pygame.draw.rect(screen, BLACK, (x, y, mini_cell_size * grid_width, mini_cell_size * grid_height))
    for row in range(grid_height):
        for col in range(grid_width):
            if grid[row][col]:
                xx = x + col * mini_cell_size
                yy = y + row * mini_cell_size
                
                (r, g, b) = get_background(grid[row][col])
                if grid[row][col].terrain == 2: (r,g,b) = (0,0,80)
                r = (1.5 * r)
                g = (1.5 * g)
                b = (1.5 * b)
                aug_cell = ceil(mini_cell_size)
                pygame.draw.rect(screen, (r, g, b), (xx, yy, aug_cell, aug_cell))
    pygame.draw.rect(screen, YELLOW, (x, y, mini_cell_size * grid_width, mini_cell_size * grid_height), 3, border_radius = 5)