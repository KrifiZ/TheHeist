# THE HEIST - Entities Module
import pygame
import math
import random
from settings import (
    TILE_SIZE, GUARD_SPEED, LASER_CYCLE, DOOR_HOLD_TIME,
    COLOR_GUARD, COLOR_DEAD_GUARD, COLOR_LASER_ACTIVE, COLOR_LASER_INACTIVE,
    COLOR_DOOR_LOCKED, COLOR_DOOR_UNLOCKED, COLOR_DIAMOND, COLOR_EXIT
)


class Guard:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.speed = GUARD_SPEED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.alive = True
        # Random initial patrol direction
        self.direction = random.choice(['left', 'right', 'up', 'down'])

    def update(self, walls):
        """Move guard in patrol direction, bounce off walls."""
        if not self.alive:
            return

        dx = 0
        dy = 0

        if self.direction == 'left':
            dx = -self.speed
        elif self.direction == 'right':
            dx = self.speed
        elif self.direction == 'up':
            dy = -self.speed
        elif self.direction == 'down':
            dy = self.speed

        # Try to move
        self.x += dx
        self.y += dy
        self.rect.x = self.x
        self.rect.y = self.y

        # Check wall collision and bounce
        for wall in walls:
            if self.rect.colliderect(wall):
                # Reverse direction
                if self.direction == 'left':
                    self.direction = 'right'
                    self.rect.left = wall.right
                elif self.direction == 'right':
                    self.direction = 'left'
                    self.rect.right = wall.left
                elif self.direction == 'up':
                    self.direction = 'down'
                    self.rect.top = wall.bottom
                elif self.direction == 'down':
                    self.direction = 'up'
                    self.rect.bottom = wall.top

                self.x = self.rect.x
                self.y = self.rect.y
                break

    def draw(self, screen, camera):
        """Draw guard (red if alive, dark grey if dead)."""
        draw_rect = camera.apply(self.rect)
        color = COLOR_GUARD if self.alive else COLOR_DEAD_GUARD
        pygame.draw.rect(screen, color, draw_rect)

    def kill(self):
        """Kill the guard."""
        self.alive = False

    def get_rect(self):
        """Return collision rect."""
        return self.rect

    def get_center(self):
        """Return center position."""
        return self.rect.center

    def is_alive(self):
        """Return alive state."""
        return self.alive


class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.active = True
        self.timer = 0

    def update(self, dt):
        """Toggle active state every LASER_CYCLE milliseconds."""
        self.timer += dt
        if self.timer >= LASER_CYCLE:
            self.timer = 0
            self.active = not self.active

    def draw(self, screen, camera):
        """Draw laser (bright red when active, dim when inactive)."""
        draw_rect = camera.apply(self.rect)
        color = COLOR_LASER_ACTIVE if self.active else COLOR_LASER_INACTIVE
        pygame.draw.rect(screen, color, draw_rect)

        # Add pulsing effect when active
        if self.active:
            pygame.draw.rect(screen, (255, 100, 100), draw_rect, 2)

    def is_dangerous(self):
        """Return True if laser is active and dangerous."""
        return self.active

    def get_rect(self):
        """Return collision rect."""
        return self.rect


class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.locked = True
        self.hold_timer = 0
        self.interaction_range = TILE_SIZE * 1.5

    def update(self, player, holding_space, dt):
        """Update door state based on player proximity and SPACE key."""
        if not self.locked:
            return 0  # Already unlocked

        # Check if player is nearby
        player_center = player.get_center()
        door_center = self.rect.center
        distance = math.sqrt(
            (player_center[0] - door_center[0]) ** 2 +
            (player_center[1] - door_center[1]) ** 2
        )

        if distance <= self.interaction_range and holding_space:
            self.hold_timer += dt
            if self.hold_timer >= DOOR_HOLD_TIME:
                self.locked = False
                self.hold_timer = DOOR_HOLD_TIME
        else:
            # Reset timer if not holding or too far
            self.hold_timer = max(0, self.hold_timer - dt * 2)  # Decay faster

        # Return progress (0.0 to 1.0) for HUD
        return self.hold_timer / DOOR_HOLD_TIME

    def draw(self, screen, camera):
        """Draw door (brown if locked, green if unlocked)."""
        draw_rect = camera.apply(self.rect)
        color = COLOR_DOOR_LOCKED if self.locked else COLOR_DOOR_UNLOCKED
        pygame.draw.rect(screen, color, draw_rect)

        if not self.locked:
            # Draw open door effect
            pygame.draw.rect(screen, (100, 200, 100), draw_rect, 2)

    def blocks_movement(self):
        """Return True if door blocks movement."""
        return self.locked

    def get_rect(self):
        """Return collision rect."""
        return self.rect

    def get_progress(self):
        """Return unlock progress (0.0 to 1.0)."""
        return self.hold_timer / DOOR_HOLD_TIME


class Diamond:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.collected = False

    def update(self, player):
        """Check if player collects the diamond."""
        if not self.collected and self.rect.colliderect(player.get_rect()):
            self.collected = True

    def draw(self, screen, camera):
        """Draw diamond if not collected."""
        if not self.collected:
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, COLOR_DIAMOND, draw_rect)
            # Add shine effect
            pygame.draw.rect(screen, (150, 255, 255), draw_rect, 2)

    def is_collected(self):
        """Return collected state."""
        return self.collected

    def get_rect(self):
        """Return collision rect."""
        return self.rect

    def reset(self):
        """Reset diamond to uncollected state."""
        self.collected = False


class Exit:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def check_win(self, player, diamond):
        """Return True if player is at exit and has diamond."""
        if diamond.is_collected() and self.rect.colliderect(player.get_rect()):
            return True
        return False

    def draw(self, screen, camera, diamond_collected=False):
        """Draw exit (brighter when diamond is collected)."""
        draw_rect = camera.apply(self.rect)
        if diamond_collected:
            # Bright green when ready to exit
            pygame.draw.rect(screen, COLOR_EXIT, draw_rect)
            pygame.draw.rect(screen, (150, 255, 150), draw_rect, 3)
        else:
            # Dim green when not ready
            pygame.draw.rect(screen, (0, 150, 0), draw_rect)

    def get_rect(self):
        """Return collision rect."""
        return self.rect
