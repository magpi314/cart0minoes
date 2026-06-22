from random import randint, choice
from collections import deque
import pygame
import ast
from math import inf

pygame.init()
pygame.mixer.init()
new_biome_sound = pygame.mixer.Sound('sound/new-biome2.wav')
new_biome_sound.set_volume(0.1)

WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
LIGHTGRAY = (190, 190, 190)
GREEN = (0, 255, 0)
BROWNGREEN = (150, 180, 0)
YELLOWGREEN = (170, 200, 0)
BLUE = (0, 0, 255)
LIGHTBLUE = (0, 180, 255)
YELLOW = (200, 200, 0)
BROWN = (150, 255, 0)
DARKGREEN = (0, 180, 0)
DEEPGREEN = (0, 127, 35) # (171,189,131) (0, 117, 94)
RED = (255, 100, 0)
DESERTRED = (255, 180, 0)

class RegionType(object):
    def __init__(
        self, name, 
        aridity_range, nullevation_range, interiority_range, on_island, in_gorge, biomass_contribution,
        chars="", color=None
    ):
        self.name = name
        self.aridity_range = aridity_range
        self.nullevation_range = nullevation_range
        self.interiority_range = interiority_range
        self.on_island = on_island
        self.in_gorge = in_gorge
        self.biomass = biomass_contribution
        self.chars = chars
        self.color = color

class Region:
    def __init__(self, label, region_type):
        self.label = label
        self.region_type = region_type
        self.cells = set()  # Using a set to avoid duplicate cells

    def add_cell(self, cell):
        self.cells.add(cell)

    def remove_cell(self, cell):
        self.cells.remove(cell)

    def __repr__(self):
        return f"Region {self.region_type.name} {self.label}, cells={len(self.cells)})"
   
#def create_region(label, biome_list):
#
#    new_region = Region(label)
#    biome_list.append(new_region)
#    return new_region

def intersection(lst1, lst2):
    return [value for value in lst1 if value in lst2]

def generate_regions(Map, region_type):

    def find_contiguous_cells(start_y, start_x, visited):
        
        def meets_criteria(cell):
            return (
                region_type.aridity_range[0] <= cell.aridity <= region_type.aridity_range[1] and
                region_type.nullevation_range[0] <= cell.nullevation <= region_type.nullevation_range[1] and
                region_type.interiority_range[0] <= cell.interiority <= region_type.interiority_range[1] and
                cell.island in region_type.on_island and
                cell.gorge in region_type.in_gorge
            )
            
        stack = [(start_y, start_x)]
        contiguous_cells = set()
        if Map[start_y][start_x].terrain == 0:
                return contiguous_cells
        while stack:
            y, x = stack.pop()
            if (y, x) in visited:
                continue

            visited.add((y, x))
            cell = Map[y][x]

            # Check if the cell meets the criteria
            if meets_criteria(cell):
                contiguous_cells.add(cell)

                # Check neighbors (ensure within bounds of the map)
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if (
                            0 <= ny < len(Map) and
                            0 <= nx < len(Map[0]) and
                            Map[ny][nx].terrain != 0 and
                            (ny, nx) not in visited
                        ):
                        stack.append((ny, nx))

        return contiguous_cells

    regions = []
    visited = set()

    for y in range(len(Map)):
        for x in range(len(Map[0])):
            if Map[y][x].terrain == 0: continue
            if (y, x) not in visited:
                contiguous_cells = find_contiguous_cells(y, x, visited)
                if len(contiguous_cells) >= 9:
                    region = Region(region_type.name, region_type)
                    for cell in contiguous_cells:
                        region.add_cell(cell)
                        if region_type.color and cell.terrain != 2:
                            cell.display = region_type.chars[hash(cell.location) % len(region_type.chars)]
                            cell.color = region_type.color
                    regions.append(region)

    return regions

def biome_metrics(Map, biome):
    rows = len(Map)
    cols = len(Map[0])
        
    def bfs(start_points):
        distances = [[float('inf')] * cols for _ in range(rows)]
        queue = deque(start_points)
        visited = set()
        for x, y in start_points:
            distances[x][y] = 0

        while queue:
            x, y = queue.popleft()
            if (x, y) not in visited:
                visited.add((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols and distances[nx][ny] == float('inf'):
                    distances[nx][ny] = distances[x][y] + 1
                    queue.append((nx, ny))
        return distances
    
    start_points = [(i, j) for i in range(rows) for j in range(cols) if Map[i][j] not in biome]
    interiority = bfs(start_points)
    I_max = max(interiority[i][j] for i in range(rows) for j in range(cols))
    Area = len(biome)
    minor_axis = 2 * I_max - 1
    major_axis = int(Area / minor_axis)

    return Area, minor_axis, major_axis

def calculate_distances(Map):
    rows, cols = len(Map), len(Map[0])
    
    aridity = [[float('inf')] * cols for _ in range(rows)]
    nullevation = [[float('inf')] * cols for _ in range(rows)]
    interiority = [[float('inf')] * cols for _ in range(rows)]
    depth = [[float('inf')] * cols for _ in range(rows)]
    
    def bfs(start_points):
        distances = [[float('inf')] * cols for _ in range(rows)]
        queue = deque(start_points)
        visited = set()
        for x, y in start_points:
            distances[x][y] = 0

        while queue:
            x, y = queue.popleft()
            if (x, y) not in visited:
                visited.add((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols and distances[nx][ny] == float('inf'):
                    distances[nx][ny] = distances[x][y] + 1
                    queue.append((nx, ny))
        return distances
    
    # Find starting points for each metric
    start_points_2 = [(i, j) for i in range(rows) for j in range(cols) if Map[i][j].terrain == 2]
    start_points_3 = [(i, j) for i in range(rows) for j in range(cols) if Map[i][j].terrain == 3]
    start_points_not_3 = [(i, j) for i in range(rows) for j in range(cols) if Map[i][j].terrain != 3]
    start_points_not_0 = [(i, j) for i in range(rows) for j in range(cols) if Map[i][j].terrain != 0]
    
    # Calculate distances for each metric
    if start_points_2:
        aridity = bfs(start_points_2)
    if start_points_3:
        nullevation = bfs(start_points_3)
    if start_points_not_3:
        interiority = bfs(start_points_not_3)
    if start_points_not_0:
        depth = bfs(start_points_not_0)

    # Combine results
    for x in range(cols):
        for y in range(rows):
            Map[y][x].aridity = aridity[y][x]
            Map[y][x].nullevation = nullevation[y][x]
            Map[y][x].interiority = interiority[y][x]
            Map[y][x].depth = depth[y][x]
    # print("-------------   aridity   -------------")
    # for _ in aridity:
    #     print(', '.join([f"{elem:03}" for elem in _]))
    # print("------------- nullevation -------------")
    # for _ in nullevation:
    #     print(', '.join([f"{elem:03}" for elem in _]))

    # print("------------- interiority -------------")
    # for _ in interiority:
    #     print(', '.join([f"{elem:03}" for elem in _]))
    # result = (aridity, nullevation, interiority)
    # return result
    
    """FIND ISLANDS AND GORGES"""
    
    def get_neighbors(row, col):
        neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return neighbors

    def flood_fill(row, col, visited, boundary):
        stack = [(row, col)] #initialize stack with coords of a valid starting cell
        cluster = [] # initialize cluster
        surrounded = True # assume it is surrounded by boundary in every direction

        while stack: # go thru stack one cell coord at a time
            r, c = stack.pop() # take a cell coord out of the stack
            if visited[r][c]: # check to see if this cell coord has already been visited
                continue # if it has been, go back to the top of the while loop
            visited[r][c] = True # now it will have been visited
            cluster.append((r, c)) # add this cell to the current working cluster

            for nr, nc in get_neighbors(r, c): # coords of neighboring cells one at a time
                if 0 <= nr < rows and 0 <= nc < cols: # check if this neighbor is within boundaries
                    terrain = Map[nr][nc].terrain # shorter name is convenient!
                    if terrain == boundary: # check if the terrain type is the boundary in question
                        continue # it hits a boundary. maintain /surrounded/ as true and get next cell coords
                    elif terrain == 0: # check if the terrain type is void
                        surrounded = False # set surrounded to false bc on this side it was not bounded
                    elif not visited[nr][nc]: # if neighbor hasn't been visited and hasn't hit a wall,
                        stack.append((nr, nc)) # then add it to the stack to check out its neighbors
                else:
                    surrounded = False # a neighbor barrier was not boundary, so surrounded is false

        return cluster, surrounded

    visited = [[False for _ in range(cols)] for _ in range(rows)]

    for row in range(rows):
        for col in range(cols):

            if not visited[row][col] and Map[row][col].terrain != 2 and Map[row][col].terrain != 0:
                cluster, is_surrounded = flood_fill(row, col, visited, 2)
                for (r, c) in cluster:
                    Map[r][c].island = is_surrounded

    visited = [[False for _ in range(cols)] for _ in range(rows)]

    for row in range(rows):
        for col in range(cols):

            if not visited[row][col] and Map[row][col].terrain != 3 and Map[row][col].terrain != 0:
                cluster, is_surrounded = flood_fill(row, col, visited, 3)
                for (r, c) in cluster:
                    Map[r][c].gorge = is_surrounded

def create_syllable():
    consonants = ["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z"]
    vowels = ["a", "e", "i", "o", "u"]
    blends = ["bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr", "sc", "sk", "sl", "sm", "sn", "sp", "st", "sw", "tr", "tw", "wh"]
    digraphs = ["ch", "sh", "th", "ph", "gh", "wh"]
    coda_clusters = ["nd", "ng", "nt", "mp", "st", "lk", "rk", "ld", "pt", "sp"]
    onset = choice(consonants + blends + digraphs + [""])
    nucleus = choice(vowels)
    coda = choice(consonants + coda_clusters + [""])
    return onset + nucleus + coda

def rand_name(syllables = 3):
    syllable_count = randint(1, syllables)
    word = "".join(create_syllable() for _ in range(syllable_count))
    return word.capitalize()

"""
("label", 
aridity_range, nullevation_range, interiority_range, interiority_range, on_island, in_gorge, biomass_contribution
display, color)
"""

file_path = 'biomes.data'
biome_list = []
with open(file_path, 'r') as file:
    for line in file:
        if line[0] == '#' or line[0] == '\n':
            continue
        #print(line)
        list_item = ast.literal_eval(line.strip())
        biome_list.append(list_item)

TERRAIN_TYPES = len(biome_list)
terrain = [None for _ in range(TERRAIN_TYPES)]
i = 0
for entry in biome_list:
    terrain[i] = RegionType(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8])
    i += 1

#print(terrain)
print(str(TERRAIN_TYPES) + " biomes found")

    #depricated regions
#terrain[n] = RegionType("savannah", (4, 9), (1, float('inf')), (0, 0), (True, True), (False, False), '..."¶', YELLOWGREEN)
#terrain[13] = RegionType("steppe", (0, 9), (1, float('inf')), (0, 0), (False, False), (True, True), '.."', YELLOW)
#terrain[6] = RegionType("barren foothills", (10, float('inf')), (1, 2), (0, 0), (False, True), (False, False), "∩..", DESERTRED)