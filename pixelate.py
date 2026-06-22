import pygame
import os

"""
<a target="_blank" href="https://icons8.com/icon/RZSnN3dwr7cT/bird">Bird</a> 
icon by <a target="_blank" href="https://icons8.com">Icons8</a>
"""

"""

i want to use this with command line arguments:

import sys

# Access command-line arguments
if len(sys.argv) < 3:
    print("Usage: python script.py <arg1> <arg2>")
    sys.exit(1)

arg1 = sys.argv[1] # argument 0 is the script name
arg2 = sys.argv[2]

print(f"Argument 1: {arg1}")
print(f"Argument 2: {arg2}")

"""

def pixelate(image, x_res, y_res):
    downsampled = pygame.transform.scale(image, (x_res, y_res))
    pixelated = pygame.transform.scale(downsampled, (50,50))
    return pixelated

pygame.init()
screen = pygame.display.set_mode((50, 50))
input_dir = "animals"
output_dir = os.path.join(input_dir, "pixelated")
os.makedirs(output_dir, exist_ok = True)
files = [f for f in os.listdir(input_dir) if f.endswith(".png")]
for filename in files:
    file_path = os.path.join(input_dir, filename)
    print(file_path)
    image = pygame.image.load(file_path).convert_alpha()
    pixelated_image = pixelate(image, 16, 16)
    new_filename = filename.replace(".png", ".bmp")
    save_path = os.path.join(output_dir, new_filename)
    pygame.image.save(pixelated_image, save_path)
    print(f"Saved: {save_path}")

pygame.quit()