# THE HEIST - Player Module
import pygame
from settings import TILE_SIZE, PLAYER_SPEED, PLAYER_RUN_SPEED, PLAYER_RUN_NOISE, COLOR_PLAYER


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.speed = PLAYER_SPEED
        self.noise_radius = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys, walls, doors=None):
        """Update player position based on input and collisions."""
        dx = 0
        dy = 0
        
        # Check for running (Shift)
        is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        
        if is_running:
            self.speed = PLAYER_RUN_SPEED
            self.noise_radius = PLAYER_RUN_NOISE
        else:
            self.speed = PLAYER_SPEED
            self.noise_radius = 0

        current_speed = self.speed

        # Handle movement input (WASD and Arrow keys)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = current_speed

        # Move horizontally and check collision
        self.x += dx
        self.rect.x = self.x

        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:  # Moving right
                    self.rect.right = wall.left
                elif dx < 0:  # Moving left
                    self.rect.left = wall.right
                self.x = self.rect.x

        # Check collision with locked doors
        if doors:
            for door in doors:
                if door.blocks_movement() and self.rect.colliderect(door.get_rect()):
                    if dx > 0:
                        self.rect.right = door.get_rect().left
                    elif dx < 0:
                        self.rect.left = door.get_rect().right
                    self.x = self.rect.x

        # Move vertically and check collision
        self.y += dy
        self.rect.y = self.y

        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:  # Moving down
                    self.rect.bottom = wall.top
                elif dy < 0:  # Moving up
                    self.rect.top = wall.bottom
                self.y = self.rect.y

        # Check collision with locked doors
        if doors:
            for door in doors:
                if door.blocks_movement() and self.rect.colliderect(door.get_rect()):
                    if dy > 0:
                        self.rect.bottom = door.get_rect().top
                    elif dy < 0:
                        self.rect.top = door.get_rect().bottom
                    self.y = self.rect.y

    def draw(self, screen, camera):
        """Draw player at camera-adjusted position."""
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, COLOR_PLAYER, draw_rect)

        # Draw noise radius when running - RED pulsing danger zone
        if self.noise_radius > 0:
            center = draw_rect.center
            # Pulsing effect - makes it clear this is dangerous
            pulse = abs(pygame.time.get_ticks() % 400 - 200) / 200  # 0 to 1
            alpha_surface = pygame.Surface((self.noise_radius * 2, self.noise_radius * 2), pygame.SRCALPHA)
            # Semi-transparent red fill
            pygame.draw.circle(alpha_surface, (255, 50, 50, int(30 + 20 * pulse)),
                             (self.noise_radius, self.noise_radius), self.noise_radius)
            # Red border
            pygame.draw.circle(alpha_surface, (255, 100, 100, int(100 + 50 * pulse)),
                             (self.noise_radius, self.noise_radius), self.noise_radius, 3)
            screen.blit(alpha_surface, (center[0] - self.noise_radius, center[1] - self.noise_radius))

    def get_rect(self):
        """Return collision rect."""
        return self.rect

    def get_center(self):
        """Return center position for distance calculations."""
        return self.rect.center

    def reset(self, x, y):
        """Reset player to spawn position."""
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

    def get_noise_radius(self):
        """Return current noise radius."""
        return self.noise_radius

    def is_sneaking(self):
        """Return True if player is sneaking (silent). For backward compatibility."""
        return self.noise_radius == 0