import os
import pygame
import json
import time
import sys

import numpy as np
from scipy.signal import convolve2d

import regions
import display_element

from map import Cell
from map import draw_minimap

pygame.init()
pygame.mixer.init()

KEY_FONT_SIZE = 20
TITLE_FONT_SIZE = 12
key_font = pygame.font.SysFont('monospace', KEY_FONT_SIZE, bold = True)
title_font = pygame.font.SysFont('monospace', TITLE_FONT_SIZE, bold = True)

place_sound = pygame.mixer.Sound('sound/place.wav')
move_sound = pygame.mixer.Sound('sound/move.wav')
switch_modes = pygame.mixer.Sound('sound/switch_modes.mp3')

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
RED = (255, 0, 0)

def draw_text(text, x, y, font = key_font, color = WHITE):

    screen = pygame.display.get_surface()
    text = str(text)
    width, height = font.size(text)

    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def show_title(x, y):

    s = ["" for _ in range(6)]

    s[0] = " _____            _                  _"
    s[1] = "/  __ \\          | |                (_)"
    s[2] = "| /  \\/ __ _ _ __| |_ ___  _ __ ___  _ _ __   ___   ___  ___  "
    s[3] = "| |    / _` | '__| __/ _ \\| '_ ` _ \\| | '_ \\ / _ \\ / _ \\/ __| "
    s[4] = "| \\__/\\ (_| | |  | || (_) | | | | | | | | | | (_) |  __/\\__ \\ "
    s[5] = " \\____/\\__,_|_|   \\__\\___/|_| |_| |_|_|_| |_|\\___/ \\___||___/ "

    for string in s:
        draw_text(string, x, y + 12 * s.index(string), font = title_font)

def save_map(Map):

    def get_input(x, y, max_char=16, prompt="Enter text:"):

        screen = pygame.display.get_surface()

        box_width = max_char * 12
        box_height = 20

        input_text = ""
        cursor_timer = time.time()
        cursor_visible = True
        active = True

        while active:
            screen.fill(BLACK)
            draw_minimap(Map, 750, 300, mini_cell_size = 4)
            
            pygame.draw.rect(screen, GRAY, (x, y, box_width, box_height))
            pygame.draw.rect(screen, WHITE, (x, y, box_width, box_height), 2)

            draw_text(input_text, x + 4, y + 4, color = BLACK)
            draw_text(prompt, x, y - 20, color = WHITE)

            if cursor_visible and len(input_text) < max_char:
                cursor_x = x + 4 + key_font.size(input_text)[0]
                cursor_y = y + 4
                pygame.draw.line(screen, RED, (cursor_x, cursor_y), (cursor_x, cursor_y + key_font.get_height()), 2)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return ""
                    elif len(input_text) < max_char:
                        input_text += event.unicode

            if time.time() - cursor_timer > 0.5:
                cursor_visible = not cursor_visible
                cursor_timer = time.time()
                
        return input_text

    def get_filename(directory="saves", prefix="map", extension=".json"):

        full_path = os.path.abspath(directory)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")
        
        for index in range(1, 1000):
            filename = f"{prefix}{index:03d}{extension}"
            file_path = os.path.join(full_path, filename)
            if not os.path.exists(file_path):
                return filename

        print("Directory full")
        return ""
    
    x = 384
    y = 390
    MAP_NAME = get_input(x, y, prompt = "Enter Region Name:")
    if MAP_NAME == "":
        return ""
    grid_width = len(Map[0])
    grid_height = len(Map)
    SAVE_LOCATION = "saves/" + get_filename()
    print(SAVE_LOCATION)
    map_json = [[cell._to_json() for cell in col] for col in Map]
    map_data = {
        'MAP_NAME' : MAP_NAME,
        'GRID_WIDTH' : grid_width,
        'GRID_HEIGHT' : grid_height,
        'cells' : map_json
    }
    with open(SAVE_LOCATION, "w") as savefile:
        json.dump(map_data, savefile, indent=3)
    return MAP_NAME, SAVE_LOCATION

def get_map(grid = [], init = False, mapname = "", filename = ""):

    def file_list(directory="saves"):

        full_path = os.path.abspath(directory)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")
        
        try:
            return os.listdir(full_path)
        except PermissionError:
            raise PermissionError(f"Access denied to the directory '{directory}'.")

    Map = []
    while Map == []:
        if init:
            screen = pygame.display.get_surface()
            screen.fill((0, 0, 0))
            background = screen.copy()
            main_menu = ["New map", "Load map", "Quit"]
        else:
            screen = pygame.display.get_surface()
            background = screen.copy()
            main_menu = ["Continue"]
            if mapname == "" or mapname == "Untitled map":
                main_menu.extend(["Save map as...", "Load map", "New map", "Quit"])
            else:
                main_menu.extend(["Save map", "Save map as...", "Load map", "New map", "Quit"])
        choice = menu(384, 300, main_menu, splash = background)
        if choice == "Save map as...":
            mapname, filename = save_map(grid)
            return None, mapname, filename
        if choice == "Save map":
            SAVE_LOCATION = filename
            print(SAVE_LOCATION)
            grid_width = len(grid[0])
            grid_height = len(grid)
            map_json = [[cell._to_json() for cell in col] for col in grid]
            map_data = {
                'MAP_NAME' : mapname,
                'GRID_WIDTH' : grid_width,
                'GRID_HEIGHT' : grid_height,
                'cells' : map_json
            }
            with open(SAVE_LOCATION, "w") as savefile:
                json.dump(map_data, savefile, indent=3)
            return None, mapname, SAVE_LOCATION
        if choice == "Continue":
            return None, mapname, filename
        elif choice == "New map":
            HEIGHT = 3 * 20
            WIDTH = 3 * 30
            Map = [[Cell((x, y)) for x in range(WIDTH)] for y in range(HEIGHT)]
            mapname = "Untitled map"
        elif choice == "Quit":
            pygame.quit()
            exit()
        elif choice == "Load map":
            load_menu = file_list()
            chosen_file = menu(750, 390, load_menu, minimap = True, splash = background)
            if chosen_file == "Continue":
                screen.blit(background, (0, 0))
                continue
            else:
                filename = "saves/" + chosen_file
            with open(filename) as savefile:
                save_data = json.load(savefile)
            mapname = save_data['MAP_NAME']
            grid_height = save_data['GRID_HEIGHT']
            grid_width = save_data['GRID_WIDTH']
            Map = [[Cell(**cell_data) for cell_data in col] for col in save_data['cells']]
            
    return Map, mapname, filename

def menu(x, y, menu_items, minimap = False, splash = None):
    def draw_menu(x, y, items, index):

        for i, item in enumerate(items):
            color = (255, 255, 0) if i == index else (255, 255, 255)
            draw_text(item, x, y + i * 30, color = color)

    selected_index = 0
    minimap_image = False

    running = True
    screen = pygame.display.get_surface()
    splash = adjust_brightness(splash, 0.5)
    splash = apply_gaussian_blur(splash)
    # splash = blurSurf(splash, 2)
    # splash = None

    pygame.event.clear()
    while running:
        if splash == None:
            screen.fill((0, 0, 0))
        else:
            screen.blit(splash, (0, 0))
        show_title(x, y)

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] > x and mouse_pos[0] < x + 200:
            selected_index = (mouse_pos[1] - y - 100) // 30 if (mouse_pos[1] - y - 100) // 30 < len(menu_items) else selected_index

        if minimap:
            
            map_menu = []
            for menu_item in menu_items:
                fname = "saves/" + menu_item
                with open(fname) as mapfile:
                    save_data = json.load(mapfile)
                try:
                    MAP_NAME = save_data['MAP_NAME']
                except:
                    MAP_NAME = menu_item
                map_menu.append(MAP_NAME)
                if menu_item == menu_items[selected_index]:
                    if minimap_image:
                        screen.blit(minimap_image, (x, y - 250))
                    else:
                        grid_height = save_data['GRID_HEIGHT']
                        grid_width = save_data['GRID_WIDTH']
                        Map = [[Cell(**cell_data) for cell_data in col] for col in save_data['cells']]
                        display_element.draw_minimap(Map, x, y - 250, mini_cell_size = 180 / grid_height)
                        minimap_image = pygame.Surface((3 * grid_width, 3 * grid_height))
                        minimap_image.blit(screen, (0,0), (x, y - 250, 3 * grid_width, 3 * grid_height))
   
            draw_menu(x, y + 100, map_menu, selected_index)
        else:
            draw_menu(x, y + 100, menu_items, selected_index)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONUP:
                pygame.mixer.Sound.play(place_sound)
                return(menu_items[selected_index])
            elif event.type == pygame.KEYDOWN:
                if not (0 <= selected_index < len(menu_items)):
                    selected_index = 0
                if event.key == pygame.K_DOWN:
                    minimap_image = False
                    selected_index = (selected_index + 1) % len(menu_items)
                    pygame.mixer.Sound.play(move_sound)
                elif event.key == pygame.K_UP:
                    minimap_image = False
                    selected_index = (selected_index - 1) % len(menu_items)
                    pygame.mixer.Sound.play(move_sound)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    pygame.mixer.Sound.play(place_sound)
                    return(menu_items[selected_index])
                elif event.key == pygame.K_ESCAPE:
                    pygame.mixer.Sound.play(switch_modes)
                    return "Continue"

        pygame.display.flip()

def adjust_brightness(surface, factor):
    """Adjust brightness of a pygame.Surface."""
    array = pygame.surfarray.pixels3d(surface)  # Get the RGB pixel array
    array = np.clip(array * factor, 0, 255).astype(np.uint8)  # Scale values and clip
    new_surface = pygame.Surface(surface.get_size())
    pygame.surfarray.blit_array(new_surface, array)
    return new_surface

def adjust_brightness_pixel_array(surface, brightness):
    """
    brightness: Brightness adjustment factor (-255 to 255).
    returns a new surface with adjusted brightness.
    """

    brightness = max(-255, min(255, brightness)) 

    new_surface = surface.copy()
    width, height = new_surface.get_size()

    for x in range(width):
        for y in range(height):
            r, g, b, a = new_surface.get_at((x, y))
            r = max(0, min(255, r + brightness))
            g = max(0, min(255, g + brightness))
            b = max(0, min(255, b + brightness))
            new_surface.set_at((x, y), (r, g, b, a))

    return new_surface

def gaussian_kernel(size, sigma):
    """    
    size: Kernel size (odd integer).
    sigma: Standard deviation of the Gaussian.
    returns a 2D numpy array representing the kernel.
    """
    ax = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / np.sum(kernel)

def apply_gaussian_blur(surface, kernel_size=5, sigma=1.0):
    """
    surface: Pygame surface to blur.
    kernel_size: Size of the Gaussian kernel (odd integer).
    sigma: Standard deviation of the Gaussian distribution.
    returns a new blurred Pygame surface.
    """
    import time

    width, height = surface.get_size()
    array = pygame.surfarray.pixels3d(surface)
    
    red, green, blue = array[:, :, 0], array[:, :, 1], array[:, :, 2]
    
    kernel = gaussian_kernel(kernel_size, sigma)
    # kernel = np.stack((kernel, kernel, kernel))
    # time.sleep(1)
    red_blurred = convolve2d(red, kernel, mode="same", boundary="wrap")
    green_blurred = convolve2d(green, kernel, mode="same", boundary="wrap")
    blue_blurred = convolve2d(blue, kernel, mode="same", boundary="wrap")
    
    blurred_array = np.stack((red_blurred, green_blurred, blue_blurred), axis=-1).astype(np.uint8)
    # array = blurred_array
    pygame.surfarray.blit_array(surface, blurred_array)
    # blurred_surface = pygame.Surface((width, height))
    # pygame.surfarray.blit_array(blurred_surface, blurred_array)
    
    return surface

def blurSurf(surface, amt):
    """
    Blur the given surface by the given 'amount'.  Only values 1 and greater
    are valid.  Value 1 = no blur.
    """
    if amt < 1.0:
        raise ValueError("Arg 'amt' must be greater than 1.0, passed in value is %s"%amt)
    scale = 1.0/float(amt)
    surf_size = surface.get_size()
    scale_size = (int(surf_size[0]*scale), int(surf_size[1]*scale))
    surf = pygame.transform.smoothscale(surface, scale_size)
    surf = pygame.transform.smoothscale(surf, surf_size)
    return surf