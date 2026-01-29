import collections
from settings import LEVELS

def find_pos(level_data, char):
    for y, row in enumerate(level_data):
        for x, col in enumerate(row):
            if col == char:
                return (x, y)
    return None

def get_neighbors(x, y, level_data):
    height = len(level_data)
    width = len(level_data[0])
    moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    neighbors = []
    
    for dx, dy in moves:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            if level_data[ny][nx] != '#':
                neighbors.append((nx, ny))
    return neighbors

def bfs(start, end, level_data):
    if not start or not end:
        return False
        
    queue = collections.deque([start])
    visited = set([start])
    
    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            return True
            
        for nx, ny in get_neighbors(x, y, level_data):
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return False

def validate_levels():
    all_valid = True
    for i, level in enumerate(LEVELS):
        print(f"Validating Level {i+1}...")
        
        start = find_pos(level, 'P')
        diamond = find_pos(level, 'D')
        exit_pos = find_pos(level, 'E')
        
        if not start:
            print(f"  Level {i+1} Error: No Player Start (P)")
            all_valid = False
            continue
        if not diamond:
            print(f"  Level {i+1} Error: No Diamond (D)")
            all_valid = False
            continue
        if not exit_pos:
            print(f"  Level {i+1} Error: No Exit (E)")
            all_valid = False
            continue
            
        # Check P -> D
        to_diamond = bfs(start, diamond, level)
        if not to_diamond:
            print(f"  Level {i+1} Error: Cannot reach Diamond from Start")
            all_valid = False
        else:
            print(f"  Path to Diamond: OK")
            
        # Check D -> E
        to_exit = bfs(diamond, exit_pos, level)
        if not to_exit:
            print(f"  Level {i+1} Error: Cannot reach Exit from Diamond")
            all_valid = False
        else:
            print(f"  Path to Exit: OK")
            
    return all_valid

if __name__ == "__main__":
    if validate_levels():
        print("\nAll levels are solvable!")
    else:
        print("\nSome levels are broken!")
