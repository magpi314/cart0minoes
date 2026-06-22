def calculate(Map):
    rows, cols = len(Map), len(Map[0])

    def get_neighbors(row, col):
        neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return [(r, c) for r, c in neighbors]

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
                        continue # this isn't necessary but i was willing to try anything when it didn't work
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

            if not visited[row][col] and Map[row][col].terrain != 3 and Map[row][col].terrain != 0:
                cluster, is_surrounded = flood_fill(row, col, visited, 3)
                for (r, c) in cluster:
                    Map[r][c].gorge = is_surrounded
