import random

WIDTH = 40
HEIGHT = 29

def generate_maze():
    # Initialize grid with walls
    # We use a grid where cells are at odd indices (1, 3, 5...)
    # Walls are at even indices.
    
    map_data = [['#' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    
    def get_neighbors(x, y):
        neighbors = []
        for dx, dy in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx < WIDTH - 1 and 1 <= ny < HEIGHT - 1:
                neighbors.append((nx, ny))
        return neighbors

    visited = set()
    stack = []
    
    # Start at 1, 1
    start_x, start_y = 1, 1
    map_data[start_y][start_x] = '.'
    visited.add((start_x, start_y))
    stack.append((start_x, start_y))
    
    while stack:
        cx, cy = stack[-1]
        neighbors = get_neighbors(cx, cy)
        unvisited = [n for n in neighbors if n not in visited]
        
        if unvisited:
            nx, ny = random.choice(unvisited)
            # Remove wall between
            wx, wy = (cx + nx) // 2, (cy + ny) // 2
            map_data[wy][wx] = '.'
            map_data[ny][nx] = '.'
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()

    # Add some loops (remove random internal walls)
    for _ in range(30):
        rx = random.randint(1, WIDTH - 2)
        ry = random.randint(1, HEIGHT - 2)
        if map_data[ry][rx] == '#':
            # Check if it connects two open spaces
            neighbors = 0
            if 0 < rx < WIDTH-1 and map_data[ry][rx-1] != '#' and map_data[ry][rx+1] != '#':
                map_data[ry][rx] = '.'
            elif 0 < ry < HEIGHT-1 and map_data[ry-1][rx] != '#' and map_data[ry+1][rx] != '#':
                map_data[ry][rx] = '.'

    # Place Entities
    # Player top left
    map_data[1][1] = 'P'
    
    # Exit bottom right
    map_data[HEIGHT-2][WIDTH-2] = 'E'
    
    # Diamond somewhere in the middle-ish or far corner
    # Let's put it in bottom left
    map_data[HEIGHT-2][1] = 'D'
    
    # Door protecting Exit? Or Diamond?
    # Let's put a door near the exit
    map_data[HEIGHT-2][WIDTH-3] = 'O'

    # Place Guards and Lasers in open spots
    empty_spots = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if map_data[y][x] == '.':
                empty_spots.append((x, y))
                
    random.shuffle(empty_spots)
    
    # Add 10 Guards
    for _ in range(10):
        if empty_spots:
            gx, gy = empty_spots.pop()
            map_data[gy][gx] = 'G'
            
    # Add 10 Lasers
    for _ in range(10):
        if empty_spots:
            lx, ly = empty_spots.pop()
            map_data[ly][lx] = 'L'

    # Print nicely formatted for python list
    print("LEVEL_2 = [")
    for row in map_data:
        print(f'    "{''.join(row)}",')
    print("]")

if __name__ == "__main__":
    generate_maze()
