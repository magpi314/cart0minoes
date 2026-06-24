import pygame
import random
import math
import json
import os

from collections import deque
from random import randint

import regions
import tiles
import menu
# import creatures
import display_element
import playlist

from map import Cell, get_background, draw_minimap
#from clouds import generate_cloud_cover

pygame.init()
pygame.mixer.init()

TILE_SIZE = 3
CELL_SIZE = 18 #px
FONT_SIZE = 18 #px
PREV_FONT_SIZE = 36
KEY_FONT_SIZE = 12
SAVE_LOCATION = "current_map.json"
TILE_LIMIT = 5
AWKWARD_SILENCE = pygame.USEREVENT + 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARKRED = (120, 0, 0)
BLUE = (0, 180, 255)
GREEN = (0, 200, 0)

EXPAND_RATIO = 0.5

screen = display_element.set_display()

font = pygame.font.SysFont('monospace', FONT_SIZE)
discovery_font = pygame.font.SysFont('monospace', KEY_FONT_SIZE, bold = True)
preview_font = pygame.font.SysFont('monospace', PREV_FONT_SIZE)
key_font = pygame.font.SysFont('monospace', KEY_FONT_SIZE, bold = True)
flavor_font = pygame.font.SysFont('monospace', KEY_FONT_SIZE, bold = True, italic = True)
error_font = pygame.font.SysFont('monospace', KEY_FONT_SIZE, bold = True)
zodiac_font = pygame.font.SysFont('monospace', PREV_FONT_SIZE)
sun_font = pygame.font.SysFont('monospace', 48)
moon_font = pygame.font.SysFont('monospace', 36)

# --- Init sounds
turn_sound = pygame.mixer.Sound('sound/turn.wav')
place_sound = pygame.mixer.Sound('sound/place.wav')
move_sound = pygame.mixer.Sound('sound/move.wav')
error_sound = pygame.mixer.Sound('sound/error.wav')
ghost_tile = pygame.mixer.Sound('sound/ghost_biome.wav')
switch_modes = pygame.mixer.Sound('sound/switch_modes.mp3')
remove_tile = pygame.mixer.Sound('sound/swoop.wav')
expand_map = pygame.mixer.Sound('sound/new-biome2.wav')

def generate_tile(grid, tile_id = 0):
    grid_width = len(grid[0])
    grid_height = len(grid)

    good_tile = False
    while not good_tile:
        tile = tiles.get_tile(random.randint(0,99)) if tile_id == 0 else tiles.get_tile(tile_id)
        colors = tiles.get_colors(tile)
        good_spaces = []
        
        if tile_id !=0:
            good_tile = True
            return tile, colors
        
        for col in range(0, grid_width, 3):
            for row in range(0, grid_height, 3):
                if (    can_place_tile(tile, colors, grid, row, col) or 
                        can_place_tile(rotate_tile(tile), colors, grid, row, col) or 
                        can_place_tile(rotate_tile(rotate_tile(tile)), colors, grid, row, col) or 
                        can_place_tile(rotate_tile(rotate_tile(rotate_tile(tile))), colors, grid, row, col)
                    ):
                    good_spaces.append([col, row])
                    good_tile = True
    return tile, colors, good_spaces

def update_map(grid, clouds):

    grid_width = len(grid[0])
    grid_height = len(grid)
    biomes = []

    def get_map_image():
        map_image = pygame.Surface((grid_width * CELL_SIZE, grid_height * CELL_SIZE))
        display_element.draw_grid(grid, clouds, 0, 0, draw_all = True, render_surface = map_image)
        return map_image
    
    def find_biomes():
        for region_type in regions.terrain:
            regionlist = regions.generate_regions(grid, region_type)
            for region in regionlist:
                biomes.append(region)
        return biomes

    def get_minimap_image():
        display_element.draw_minimap(grid, 50, 50)
        minimap_image = pygame.Surface((3 * grid_width, 3 * grid_height))
        minimap_image.blit(screen, (0,0), (50, 50, 3 * grid_width, 3 * grid_height))
        return minimap_image

    find_impossible_voids(grid)
    regions.calculate_distances(grid)
    biomes = find_biomes()
    map_image = get_map_image()
    minimap_image = get_minimap_image()

    return grid, biomes, map_image, minimap_image

def discovered(biomes):
    disco = []
    for biome in biomes:
        if biome.label not in disco:
            disco.append(biome.label)
    disco.sort()
    return disco

def construct_tile(grid, row, col):
    
    grid_width = len(grid[0])
    grid_height = len(grid)

    directions = [(0, 1), (1, 2), (2, 1), (1, 0)]
    Default = Cell((1, 1), terrain = 1, display = ".", color = (150, 255, 0))
    
    # first, make four sides match adjacent

    if row - 1 >= 0:
        grid[row][col + 1] = grid[row - 1][col + 1] if grid[row - 1][col + 1].terrain != 0 else Default
    else:
        grid[row][col + 1] = Default
    if col + 3 <= grid_width - 1:
        grid[row + 1][col + 2] = grid[row + 1][col + 3] if grid[row + 1][col + 3].terrain != 0 else Default
    else:
        grid[row + 1][col + 2] = Default
    if row + 3 <= grid_height - 1:
        grid[row + 2][col + 1] = grid[row + 3][col + 1] if grid[row + 3][col + 1].terrain != 0 else Default
    else:
        grid[row + 2][col + 1] = Default
    if col - 1 >= 0:
        grid[row + 1][col] = grid[row + 1][col - 1] if grid[row + 1][col - 1].terrain != 0 else Default
    else:
        grid[row + 1][col] = Default
    grid[row + 1][col + 1] = Default

    #if there are any rivers, the middle is a lake or a confluence if i decide to get fancy
    if any(grid[row + directions[_][0]][col + directions[_][1]].terrain == 1 for _ in range(4)):
        grid[row + 1][col + 1] = Cell((col + 1, row + 1), terrain = 2, display = "█", color = (0, 0, 255))

    #the middle is a mountain if there are 2 or 4 mountains but not if there are 4
    mountains = 0
    for _ in range(4):
        if grid[row + directions[_][0]][col + directions[_][1]].terrain == 3: mountains += 1
    if mountains == 2 or mountains == 4:
        grid[row + 1][col + 1] = Cell((col + 1, row + 1), terrain = 3, display = "Δ", color = (150, 150, 150))

    #corners are the same as the adjacent sides if they're identical, otherwise it's grass
    grid[row][col] = Default
    grid[row][col + 2] = Default
    grid[row + 2][col + 2] = Default
    grid[row + 2][col] = Default
    if grid[row][col + 1].display == grid[row + 1][col].display:
        grid[row][col] = grid[row][col + 1]
    if grid[row][col + 1].display == grid[row + 1][col + 2].display:
        grid[row][col + 2] = grid[row][col + 1]
    if grid[row + 2][col + 1].display == grid[row + 1][col + 2].display:
        grid[row + 2][col + 2] = grid[row + 2][col + 1]
    if grid[row + 2][col + 1].display == grid[row + 1][col].display:
        grid[row + 2][col + 0] = grid[row + 2][col + 1]

    #rectify coordinates
    for i in range(2):
        for j in range(2):
            grid[row + i][col + j].location = (col + i, row + j)
    #should just return tile, colors

def find_impossible_voids(grid):
    t = [None for _ in range(9)]
    directions = [(-1, 1), (3, 1), (1, 3), (1, -1)]
    grid_width = len(grid[0])
    grid_height = len(grid)
    for col in range(0, grid_width, 3):
        for row in range(0, grid_height, 3):
            unfit_tiles = 0
            neighbors = []
            for d in directions:
                if 0 <= row + d[0] <= grid_height - 1 and 0 <= col + d[1] <= grid_width - 1:
                    neighbors.append(grid[row + d[0]][col + d[1]].terrain)
                else:
                    neighbors.append(0)

            if grid[row][col].terrain == 0 and any(neighbors) != 0: # if cell is empty but not all neighbors are
                for i in range(tiles.TILE_TYPES):
                    t = list(tiles.s[i][_] for _ in range(9))
                    tile =((t[0],t[1],t[2]),(t[3],t[4],t[5]),(t[6],t[7],t[8]))
                    colors = tiles.get_colors(tile)
                    if not (can_place_tile(tile, colors, grid, row, col) or 
                            can_place_tile(rotate_tile(tile), colors, grid, row, col) or 
                            can_place_tile(rotate_tile(rotate_tile(tile)), colors, grid, row, col) or 
                            can_place_tile(rotate_tile(rotate_tile(rotate_tile(tile))), colors, grid, row, col)
                           ):
                        unfit_tiles += 1
                    #print(str(unfit_tiles))
                    if unfit_tiles == tiles.TILE_TYPES: # none of the tiles work here
                        #print("constructing tile")
                        pygame.mixer.Sound.play(ghost_tile)
                        construct_tile(grid, row, col) 
                        # i need to make this return tile,colors, and then place_tile()
    return True

def place_tile(Map, cur_tile, cur_colors, sel_row, sel_col):

    if all(cell.terrain != 0 for row in Map for cell in row):
        return Map #does not place tile if whole map is full

    for i in range(TILE_SIZE):
        for j in range(TILE_SIZE):
            ter = 0
            if cur_tile[i][j] in tiles.passable: ter = 1
            if cur_tile[i][j] in tiles.impassable: ter = 2
            if cur_tile[i][j] == "Δ": ter = 3
            Map[sel_row+i][sel_col+j] = Cell(
                (sel_col + j, sel_row + i), 
                terrain = ter, 
                display = cur_tile[i][j], 
                color = cur_colors[i][j]
            )
    return Map

def can_place_tile(tile, colors, grid, row, col): # colors is included so it can receive the output of rotate_tile()
    # ERROR MESSAGES ARE GENERATED BUT NOT RETURNED BECAUSE
    # RETURNING THE ERRORMESSAGE CAUSES IT TO PERMIT INCORRECT TILE PLACEMENTS

    grid_width = len(grid[0])
    grid_height = len(grid)

    if all(cell.terrain != 0 for row in grid for cell in row):
        return True

    #check if selected area is empty
    for i in range(TILE_SIZE):
        for j in range(TILE_SIZE):
            if grid[row + i][col + j].terrain != 0:
                errormessage = "Must place tile on empty space"
                return False
    
    land = [None for _ in range(4)]
    neighbor = [None for _ in range(4)]
    #land = [[None for _ in range(4)] for _ in range(4)]
    #neighbor = [[None for _ in range(4)] for _ in range(4)]
    
    NORTH, SOUTH, EAST, WEST = range(4)
            
    land[NORTH] = tile[0][1]
    land[SOUTH] = tile[2][1]
    land[EAST] = tile[1][2]
    land[WEST] = tile[1][0]
    
    if row - 1 >= 0 and col + 1 <= grid_width - 1:
        neighbor[NORTH] = grid[row-1][col+1].display if grid[row-1][col+1].terrain != 0 else None
    if row + 3 <= grid_height - 1 and col + 1 <= grid_width - 1:
        neighbor[SOUTH] = grid[row+3][col+1].display if grid[row+3][col+1].terrain != 0 else None
    if row + 1 <= grid_height - 1 and col + 3 <= grid_width - 1:
        neighbor[EAST] = grid[row+1][col+3].display if grid[row+1][col+3].terrain != 0 else None
    if row + 1 <= grid_height - 1 and col - 1 >= 0:
        neighbor[WEST] = grid[row+1][col-1].display if grid[row+1][col-1].terrain != 0 else None

    # impassable lands must align, but passable lands may be adjacent to one another
    if any(land[x] != neighbor[x] and neighbor[x] != None and (land[x] in tiles.impassable or neighbor[x] in tiles.impassable) for x in range(4)):
        errormessage = "Tile must be adjacent to matching tile"
        return False

    #check to be sure that there is at least one adjacent tile
    if all(neighbor[i] == None for i in range(4)): 
        errormessage = "Tile must be adjacent to matching tile"
        return False

    return True
    
def rotate_tile(tile):
    new_tile = [[None for _ in range(TILE_SIZE)] for _ in range(TILE_SIZE)]
    new_tile[0][0] = tile[2][0]
    new_tile[1][0] = tile[2][1]
    new_tile[2][0] = tile[2][2]
    new_tile[0][1] = tile[1][0]
    new_tile[1][1] = tile[1][1]
    new_tile[2][1] = tile[1][2]
    new_tile[0][2] = tile[0][0]
    new_tile[1][2] = tile[0][1]
    new_tile[2][2] = tile[0][2]
    
    #then rotate river segments
    for i in range(TILE_SIZE):
        for j in range(TILE_SIZE):
            if new_tile[i][j] == "║":
                new_tile[i][j] = "═"
            elif new_tile[i][j] == "═":
                new_tile[i][j] = "║"
    if new_tile[1][1] == "╔":
        new_tile[1][1] = "╗"
    elif new_tile[1][1] == "╗":
        new_tile[1][1] = "╝"
    elif new_tile[1][1] == "╝":
        new_tile[1][1] = "╚"
    elif new_tile[1][1] == "╚":
        new_tile[1][1] = "╔"
    return new_tile

def draw_animal(x, y, fileno):
    def file_list(directory="animals/pixelated"):

        full_path = os.path.abspath(directory)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")
        
        try:
            return os.listdir(full_path)
        except PermissionError:
            raise PermissionError(f"Access denied to the directory '{directory}'.")

    files = file_list()
    image_name = files[fileno]
    filename = os.path.join('animals/pixelated', image_name)
    image = pygame.image.load(filename).convert()
    screen.blit(image, (x, y))

def quicksave(Map):
    grid_width = len(Map[0])
    grid_height = len(Map)
    map_json = [[cell._to_json() for cell in col] for col in Map]
    map_data = {
        'grid_width' : grid_width,
        'grid_height' : grid_height,
        'cells' : map_json
    }
    with open(SAVE_LOCATION, "w") as savefile:
        json.dump(map_data, savefile, indent=3)

def grabbed_tile(grid, selected_row, selected_col):
    t = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if grid[selected_row + i][selected_col + j].terrain == 1:
                t[i][j] = "."
            elif grid[selected_row + i][selected_col + j].terrain == 2:
                if (i, j) == (0, 1) or (i, j) == (2, 1):
                    t[i][j] = "║"
                elif (i, j) == (1, 0) or (i, j) == (1, 2):
                    t[i][j] = "═"
                elif (i, j) == (1, 1):
                    if grid[selected_row + 0][selected_col + 1].terrain == 2: 
                        if grid[selected_row + 1][selected_col + 0].terrain == 2:
                            t[i][j] = "╝"
                        elif grid[selected_row + 1][selected_col + 2].terrain == 2:
                            t[i][j] = "╚"
                        elif grid[selected_row + 2][selected_col + 1].terrain == 2:
                            t[i][j] = "║"
                        else:
                            t[i][j] = "█"
                    elif grid[selected_row + 2][selected_col + 1].terrain == 2:
                        if grid[selected_row + 1][selected_col + 0].terrain == 2:
                            t[i][j] = "╗"
                        elif grid[selected_row + 1][selected_col + 2].terrain == 2: # ONLY ONE THAT WORKS
                            t[i][j] = "╔"
                        elif grid[selected_row + 0][selected_col + 1].terrain == 2:
                            t[i][j] = "║"
                        else:
                            t[i][j] = "█"
                    elif grid[selected_row + 1][selected_col + 0].terrain == 2 and grid[selected_row + 1][selected_col + 2].terrain == 2:
                        t[i][j] = "═"
            elif grid[selected_row + i][selected_col + j].terrain == 3:
                t[i][j] = "Δ"
    return t

def quickload():
    with open(SAVE_LOCATION) as savefile:
        save_data = json.load(savefile)
    Map = [[Cell(**cell_data) for cell_data in col] for col in save_data['cells']]
    return Map

def main():

    # Initialize game state
    grid, mapname, filename = menu.get_map(init = True)
    grid_width = len(grid[0])
    grid_height = len(grid)
    clouds = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
    biomes = []
    discoveries = []
    views = ["default", "elevation", "humidity", "biome"]
    view = 0
    selected_biome = None
    selected_biome_name = ""
    old_tile, old_colors = deque(), deque()
    hand = []
    area_filled = 0

    screen_info = pygame.display.Info()
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_info.current_w, screen_info.current_h

    music_files = [f for f in os.listdir("music") if f.endswith((".mp3", ".wav", ".ogg"))]
    current_song = playlist.play_music(music_files)
    pygame.mixer.music.set_endevent(AWKWARD_SILENCE)
    playlist.get_songname(current_song)

    #place first tile (sacred spring)
    selected_row, selected_col = int(grid_height / 6) * 3, int(grid_width / 6) * 3 #place cursor in center of map
    if grid[selected_row][selected_col].terrain == 0: # if center of map is empty, must place sacred spring
        current_tile, current_colors = generate_tile(grid, tile_id = 100)
        place_tile(grid, current_tile, current_colors, selected_row, selected_col)
    grid, biomes, map_image, minimap_image = update_map(grid, clouds)
    #biomass = sum((biome.region_type.biomass * len(biome.cells)) for biome in biomes)
    discoveries = discovered(biomes)

    playing = True
    selected_row = int(grid_height / 6) * 3
    selected_col = int(grid_width / 6) * 3
    current_tile, current_colors, good_spaces = generate_tile(grid)

    currentx, currenty = (
        (SCREEN_WIDTH / 2)  - CELL_SIZE * (1.5 + selected_col), 
        (SCREEN_HEIGHT / 2) - CELL_SIZE * (1.5 + selected_row)
    )

    dragx, dragy = 0, 0
    dragging = False
    draw_card = False
    selected_card = None
    delay = 250 
    show = True
    change_time = pygame.time.get_ticks() + delay
    automated = False
    frame = 0

    pygame.key.set_repeat(300, 80)

    while playing:
        frame += 1
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == AWKWARD_SILENCE:
                current_song = playlist.play_music(music_files, current_song = current_song)
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.VIDEORESIZE:
                screen_info = pygame.display.Info()
                SCREEN_WIDTH, SCREEN_HEIGHT = screen_info.current_w, screen_info.current_h
            if event.type == pygame.MOUSEBUTTONDOWN:
                if SCREEN_WIDTH - 160 <= mouse_pos[0] <= SCREEN_WIDTH - 50:
                    for i in range(len(hand)):
                        if 168 + 113 * i <= mouse_pos[1] <= 274 + 113 * i:
                            draw_card = True
                            selected_card = i
                            card_offset = (SCREEN_WIDTH - 160 - mouse_pos[0], (168 + 113 * i) - mouse_pos[1])
                    if draw_card == False:
                        dragging = True
                else:
                    dragging = True
                dragx, dragy = mouse_pos[0], mouse_pos[1]
            if event.type == pygame.MOUSEBUTTONUP:
                if draw_card:                    
                    if highlight:
                        biome_list = [biome for biome in biomes if grid[highlight_row][highlight_col] in biome.cells]
                        for biome in biome_list:
                            if biome.label in hand[selected_card][1]:
                                pygame.mixer.Sound.play(expand_map)
                                hand[selected_card] = (creatures.creature[randint(0, len(creatures.creature))])

                dragging = False
                draw_card = False
                selected_card = None
                if (dragx, dragy) == (mouse_pos[0], mouse_pos[1]):
                    #that was a click
                    continue
                elif (dragx, dragy) != (mouse_pos[0], mouse_pos[1]):
                    dragx, dragy = 0, 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                    print("Toggling fullscreen")
                    pygame.display.toggle_fullscreen()
                    screen_info = pygame.display.Info()
                    SCREEN_WIDTH, SCREEN_HEIGHT = screen_info.current_w, screen_info.current_h
                elif event.key == pygame.K_TAB:
                    if len(old_tile) == TILE_LIMIT - 1:
                        pygame.mixer.Sound.play(error_sound)
                    else:
                        next_tile, next_colors, good_spaces = generate_tile(grid)
                        old_tile.appendleft(current_tile)
                        old_colors.appendleft(current_colors)
                        current_tile = next_tile
                        current_colors = next_colors
                        pygame.mixer.Sound.play(remove_tile)
                        # fgrid, fbiomes, map_image, fminimap_image = update_map(grid, clouds)
                        # del fgrid, fbiomes, fminimap_image             
                elif event.key == pygame.K_BACKSPACE:
                    if grid[selected_row][selected_col].terrain == 0 or len(old_tile) == TILE_LIMIT - 1:
                        pygame.mixer.Sound.play(error_sound)
                    else:
                        old_tile.appendleft(current_tile)
                        old_colors.appendleft(current_colors)
                        pygame.mixer.Sound.play(remove_tile)
                        tile = grabbed_tile(grid, selected_row, selected_col)
                        for i in range(3):
                            for j in range(3):
                                grid[selected_row + i][selected_col + j] = Cell((selected_col + j, selected_row + i))
                        current_tile = tuple(tile)
                        current_colors = tiles.get_colors(current_tile)
                        grid, biomes, map_image, minimap_image = update_map(grid, clouds)
                        # del fgrid, fbiomes, fminimap_image
                elif event.key == pygame.K_F3:
                    automated = not automated
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    pygame.mixer.Sound.play(move_sound)
                    selected_row = (selected_row - TILE_SIZE) % grid_height
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    pygame.mixer.Sound.play(move_sound)
                    selected_row = (selected_row + TILE_SIZE) % grid_height
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    pygame.mixer.Sound.play(move_sound)
                    selected_col = (selected_col - TILE_SIZE) % grid_width
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    pygame.mixer.Sound.play(move_sound)
                    selected_col = (selected_col + TILE_SIZE) % grid_width
                elif event.key == pygame.K_v:
                    view = (view + 1) % 4
                elif event.key == pygame.K_e:
                    pygame.mixer.Sound.play(turn_sound)
                    current_tile = rotate_tile(current_tile)
                    current_colors = rotate_tile(current_colors)
                elif event.key == pygame.K_q:
                    pygame.mixer.Sound.play(turn_sound)
                    current_tile = rotate_tile(current_tile)
                    current_tile = rotate_tile(current_tile)
                    current_tile = rotate_tile(current_tile) #this is a sad solution but whatever
                    current_colors = rotate_tile(current_colors) #can i cleverly define a counterclockwise modifier for this function?
                    current_colors = rotate_tile(current_colors)
                    current_colors = rotate_tile(current_colors)
                elif event.key == pygame.K_F5:
                    quicksave(grid)
                elif event.key == pygame.K_F9:
                    grid = quickload()
                    grid_height = len(grid)
                    grid_width = len(grid[0])
                    current_tile, current_colors, good_spaces = generate_tile(grid)
                    grid, biomes, map_image, minimap_image = update_map(grid, clouds)
                    discoveries = discovered(biomes)
                elif event.key == pygame.K_0: #pause song
                    playlist.toggle_pause()
                elif event.key == pygame.K_MINUS: # prev song
                    if music_files:
                        current_song = playlist.play_music(music_files, current_song = current_song, mode = -1)
                    else:
                        music_files = [f for f in os.listdir("music") if f.endswith((".mp3", ".wav", ".ogg"))]
                        current_song = playlist.play_music(music_files, current_song = current_song, mode = -1)
                elif event.key == pygame.K_EQUALS: # next song
                    if music_files:
                        current_song = playlist.play_music(music_files, current_song = current_song)
                    else:
                        music_files = [f for f in os.listdir("music") if f.endswith((".mp3", ".wav", ".ogg"))]
                        current_song = playlist.play_music(music_files, current_song = current_song)
                elif event.key == pygame.K_ESCAPE:
                    playlist.toggle_pause()
                    pygame.mixer.Sound.play(switch_modes)
                    new_grid, mapname, filename = menu.get_map(grid, mapname = mapname, filename = filename)
                    playlist.toggle_pause()
                    if new_grid == None:
                        continue
                    else:
                        grid = new_grid
                        grid_width = len(grid[0])
                        grid_height = len(grid)
                        biomes = []
                        view = 0

                        grid, biomes, map_image, minimap_image = update_map(grid, clouds)
                        
                        #must place sacred spring if it returns an empty map!
                        if all(grid[x][y].terrain == 0 for x in range(len(grid)) for y in range(len(grid[x]))):
                            selected_row, selected_col = int(grid_height / 6) * 3, int(grid_width / 6) * 3
                            current_tile, current_colors = generate_tile(grid, tile_id = 100)
                            place_tile(grid, current_tile, current_colors, selected_row, selected_col)
                            current_tile, current_colors, good_spaces = generate_tile(grid)
                        grid, biomes, map_image, minimap_image = update_map(grid, clouds)
                        discoveries = discovered(biomes)
                
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if can_place_tile(current_tile, current_colors, grid, selected_row, selected_col):
                        pygame.mixer.Sound.play(place_sound)
                        grid = place_tile(grid, current_tile, current_colors, selected_row, selected_col)
                        area_filled = 0
                        for row in range(grid_height):
                            for col in range(grid_width):
                                if grid[row][col].terrain != 0:
                                    area_filled += 1
                                                
                        if len(old_tile) > 0:
                            current_tile, current_colors = old_tile.popleft(), old_colors.popleft()
                        else:
                            current_tile, current_colors, good_spaces = generate_tile(grid)
                        grid, biomes, map_image, minimap_image = update_map(grid, clouds)
                        discoveries = discovered(biomes)

                    else:
                        pygame.mixer.Sound.play(error_sound)

        if dragging:
            dx = mouse_pos[0] - dragx
            dy = mouse_pos[1] - dragy
            if dx >= CELL_SIZE * TILE_SIZE:
                dragx = mouse_pos[0]
                selected_col = (selected_col - TILE_SIZE) % grid_width
            if dx <= - CELL_SIZE * TILE_SIZE:
                dragx = mouse_pos[0]
                selected_col = (selected_col + TILE_SIZE) % grid_width
            if dy >= CELL_SIZE * TILE_SIZE:
                dragy = mouse_pos[1]
                selected_row = (selected_row - TILE_SIZE) % grid_height
            if dy <= -CELL_SIZE * TILE_SIZE:
                dragy = mouse_pos[1]
                selected_row = (selected_row + TILE_SIZE) % grid_height

        if automated: # THIS DOESNT REALLY WORK ANYMORE
            coords = good_spaces[randint(0, len(good_spaces) - 1)]
            selected_row = coords[1]
            selected_col = coords[0]

            while not can_place_tile(current_tile, current_colors, grid, selected_row, selected_col):
                pygame.mixer.Sound.play(turn_sound)
                current_tile = rotate_tile(current_tile)
                current_colors = rotate_tile(current_colors)

            pygame.mixer.Sound.play(place_sound)
            place_tile(grid, current_tile, current_colors, selected_row, selected_col)

            current_tile, current_colors, good_spaces = generate_tile(grid)
            grid, biomes, map_image, minimap_image = update_map(grid, clouds)
            discoveries = discovered(biomes)

            #automated = False #restore this line to automate one step at a time

        if area_filled / (grid_height * grid_width) >= EXPAND_RATIO:
            grid_height += 6
            grid_width += 6
            new_grid = [[Cell((x, y)) for x in range(grid_width)] for y in range(grid_height)]
            clouds = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
            for row in range(3, grid_height - 3):
                for col in range(3, grid_width - 3):
                    new_grid[row][col] = grid[row - 3][col - 3]
                    new_grid[row][col].location = (col, row)
            grid = new_grid
            grid, biomes, map_image, minimap_image = update_map(grid, clouds)
            selected_row +=3
            selected_col +=3
            currentx, currenty = (
                (SCREEN_WIDTH / 2)  - CELL_SIZE * (1.5 + selected_col), 
                (SCREEN_HEIGHT / 2) - CELL_SIZE * (1.5 + selected_row)
            )

        targetx, targety = (
            (SCREEN_WIDTH / 2)  - CELL_SIZE * (1.5 + selected_col), 
            (SCREEN_HEIGHT / 2) - CELL_SIZE * (1.5 + selected_row)
        )

        dx, dy = targetx - currentx, targety - currenty

        if abs(dx) <= CELL_SIZE/2 and abs(dy) <= CELL_SIZE/2:
            currentx, currenty = targetx, targety
        else:
            currentx += dx // 8
            currenty += dy // 8            
        if currentx == targetx and currenty == targety and dragging == False:  #don't draw highlight when moving
            highlight_row = int((mouse_pos[1] - currenty - 3) / CELL_SIZE)
            highlight_col = int((mouse_pos[0] - currentx - 3) / CELL_SIZE)
            
            if 0 <= highlight_row < grid_height and 0 <= highlight_col < grid_width:
                highlight = (highlight_row, highlight_col)
            else:
                highlight = False
        else:
            highlight = False

        # addclouds = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
        # for row in range(1, grid_height - 1):
        #     for col in range(1, grid_width - 1):
        #         cel = grid[row][col]
        #         addclouds[row][col] += max(0, 2 * (cel.nullevation - cel.interiority - cel.aridity)) #accumulation
        #         wind_velocity = int((cel.aridity + cel.nullevation + cel.interiority) / 5)
        #         del_Prow = (
        #             (grid[row + 1][col].nullevation - grid[row + 1][col].interiority) -
        #             (grid[row - 1][col].nullevation - grid[row - 1][col].interiority)
        #         )
        #         del_Pcol = (
        #             (grid[row][col + 1].nullevation - grid[row][col + 1].interiority) -
        #             (grid[row][col - 1].nullevation - grid[row][col - 1].interiority)
        #             + wind_velocity
        #         )
        #         del_Prow = int(abs(del_Prow) / del_Prow) if del_Prow != 0 else 0
        #         del_Pcol = int(abs(del_Pcol) / del_Pcol) if del_Pcol != 0 else 0
        #         if not (0 <= row + del_Prow < grid_height and 0 <= col + del_Pcol < grid_width):
        #             addclouds[row][col] -= clouds[row][col]
        #         else:
        #             addclouds[row + del_Prow][col + del_Pcol] += clouds[row][col]
        #             addclouds[row][col] -= clouds[row][col]

        # for row in range(grid_height):
        #     for col in range(grid_width):
        #         cel = grid[row][col]
        #         clouds[row][col] += addclouds[row][col]
                # threshold = 5 + cel.interiority - cel.nullevation - cel.aridity
                # if clouds[row][col] > threshold:
                #     precip = max(
                #         clouds[row][col], 
                #         min(0, 
                #             (clouds[row][col] / 255) * (cel.nullevation - cel.interiority - cel.aridity) / 5
                #         )
                #     )
                #     clouds[row][col] -= precip
        #         clouds[row][col] = max(clouds[row][col], 0)
        # clouds = cloud_operations.diffuse_moisture(clouds)

        # del addclouds

        #update display
        screen.fill(BLACK)

        if map_image:
            screen.blit(map_image, (currentx, currenty))

        display_element.draw_curtile(screen, grid, currentx, currenty, 
            selrow = selected_row, selcol = selected_col, 
            curtile = current_tile, curcolors = current_colors, 
            show = show, can_place_tile = can_place_tile(current_tile, current_colors, grid, selected_row, selected_col)
        )
        
        if highlight:
            display_element.draw_biome(screen, grid, currentx, currenty, highlight, biomes = biomes, view = view)

        current_time = pygame.time.get_ticks()

        if current_time >= change_time:
            change_time = current_time + delay
            show = not show
        cursorx, cursory = (SCREEN_WIDTH / 2) - CELL_SIZE * 1.5, (SCREEN_HEIGHT / 2) - CELL_SIZE * 1.5
        if show:
            pygame.draw.rect(screen, RED, (cursorx, cursory, TILE_SIZE * CELL_SIZE, TILE_SIZE * CELL_SIZE), 2, border_radius = 3)
        else:
            pygame.draw.rect(screen, DARKRED, (cursorx, cursory, TILE_SIZE * CELL_SIZE, TILE_SIZE * CELL_SIZE), 1, border_radius = 3)

        x = SCREEN_WIDTH - 50 - PREV_FONT_SIZE * 3
        y = 50
        for i in range(len(old_tile)):
            nx = x - 138 * (len(old_tile) - i - 1)
            ny = y
            display_element.draw_preview_tile(screen, old_tile[i], old_colors[i], nx, ny)
        display_element.draw_preview_tile(screen, current_tile, current_colors, x - 138 * (len(old_tile)), y, active = True)


        screen.blit(minimap_image, (50, 50))
        text_surface = preview_font.render(mapname, True, WHITE)
        screen.blit(text_surface, (50, 10))
        selected_biome_name = ""
        if highlight:
            for biome in biomes:
                if grid[highlight[0]][highlight[1]] in biome.cells:
                    selected_biome_name = biome.label
                    selected_biome = biome
                    break

        # handsize = 4
        # if len(hand) <= handsize:
        #     hand.append(creatures.creature[randint(0, len(creatures.creature) - 1)]) # could be replaced by some kind of combinatoric thing?
        # for i in range(len(hand)):
        #     x = SCREEN_WIDTH - 130
        #     y = 218 + 113 * i
        #     if selected_card != i:
        #         pygame.draw.rect(screen, BLACK, (x - 30, y - 50, 110, 106))
        #         text_surface = discovery_font.render(hand[i][0], True, WHITE)
        #         screen.blit(text_surface, (x - 25, y - 45))
        #         draw_animal(x, y, i)
        #         pygame.draw.rect(screen, WHITE, (x - 30, y - 50, 110, 106), 2, border_radius=3)

        # if draw_card:
        #     (x, y) = (a + b for a, b in zip(mouse_pos, card_offset))
        #     pygame.draw.rect(screen, BLACK, (x, y, 110, 106))
        #     text_surface = discovery_font.render(hand[selected_card][0], True, WHITE)
        #     screen.blit(text_surface, (x + 5, y + 5))
        #     # draw_animal(x + 30, y + 50, selected_card)
        #     pygame.draw.rect(screen, WHITE, (x, y, 110, 106), 2, border_radius=3)

        y, i = 250, -16
        for biome in discoveries:
            i += 16
            fontcolor = WHITE if biome == selected_biome_name else GREEN
            text_surface = discovery_font.render(biome, True, fontcolor)
            screen.blit(text_surface, (50, y + i))

        day = frame / 100
        quarter = int((day % 365) / (365 / 4))
        phase = int((day % 28) / 7)
        season = ["spring", "summer", "autumn", "winter"]
        moon = "○◑●◐"
        season_text = season[quarter]
        moon_pic = moon[phase]
        display_element.draw_text(screen, season_text, (SCREEN_WIDTH / 2) - len(season_text) * 36, 0)
        display_element.draw_text(screen, moon_pic, SCREEN_WIDTH / 2, 0)

        baserate = EXPAND_RATIO * (grid_height - 6) * (grid_width - 6) / (grid_width * grid_height)
        acturate = area_filled / (grid_height * grid_width)
        perc = (acturate - baserate) / (EXPAND_RATIO - baserate)
        pygame.draw.rect(screen, WHITE, ((SCREEN_WIDTH / 2) - 500, SCREEN_HEIGHT - 100, 1000, 50), width = 4, border_radius = 4)
        pygame.draw.rect(screen, RED, ((SCREEN_WIDTH / 2) - 490, SCREEN_HEIGHT - 90, perc * (1000-20), 30))

        txt = "" #this should display errormessage, which is given by can_place_tile
        text_surface = error_font.render(txt + " " * (43 - len(txt)), True, BLACK, RED)
        if txt != "": 
            screen.blit(text_surface,(grid_width * CELL_SIZE + 17, 76 + 92 + 66))

        pygame.display.flip()

if __name__=="__main__":
    main()
    pygame.quit()
