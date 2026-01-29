# THE HEIST - Level Module
import pygame
from settings import TILE_SIZE, COLOR_WALL, MAP_DATA


class Level:
    def __init__(self):
        self.walls = []
        self.spawn_points = {
            'player': None,
            'guards': [],
            'diamond': None,
            'exit': None,
            'lasers': [],
            'doors': []
        }
        self._parse_map()

    def _parse_map(self):
        """Parse MAP_DATA and create wall rects and spawn points."""
        for row_idx, row in enumerate(MAP_DATA):
            for col_idx, tile in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE

                if tile == '#':
                    # Wall
                    wall_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.walls.append(wall_rect)
                elif tile == 'P':
                    # Player spawn
                    self.spawn_points['player'] = (x, y)
                elif tile == 'G':
                    # Guard spawn
                    self.spawn_points['guards'].append((x, y))
                elif tile == 'D':
                    # Diamond
                    self.spawn_points['diamond'] = (x, y)
                elif tile == 'E':
                    # Exit
                    self.spawn_points['exit'] = (x, y)
                elif tile == 'L':
                    # Laser
                    self.spawn_points['lasers'].append((x, y))
                elif tile == 'O':
                    # Door
                    self.spawn_points['doors'].append((x, y))

    def get_walls(self):
        """Return list of wall rects."""
        return self.walls

    def get_spawn_points(self):
        """Return dictionary of spawn points."""
        return self.spawn_points

    def draw(self, screen, camera):
        """Draw all wall rects."""
        for wall in self.walls:
            draw_rect = camera.apply(wall)
            # Only draw walls that are visible on screen
            if (draw_rect.right > 0 and draw_rect.left < camera.width and
                draw_rect.bottom > 0 and draw_rect.top < camera.height):
                pygame.draw.rect(screen, COLOR_WALL, draw_rect)
