# THE HEIST - Camera Module
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

    def update(self, player):
        """Center camera on player, clamped to world bounds."""
        # Calculate desired camera position (centered on player)
        target_x = player.rect.centerx - self.width // 2
        target_y = player.rect.centery - self.height // 2

        # Clamp to world bounds
        self.offset_x = max(0, min(target_x, WORLD_WIDTH - self.width))
        self.offset_y = max(0, min(target_y, WORLD_HEIGHT - self.height))

    def apply(self, rect):
        """Return screen-space rect for drawing."""
        return pygame.Rect(
            rect.x - self.offset_x,
            rect.y - self.offset_y,
            rect.width,
            rect.height
        )

    def apply_pos(self, x, y):
        """Apply camera offset to a position."""
        return (x - self.offset_x, y - self.offset_y)
