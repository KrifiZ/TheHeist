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

    def _get_all_blockers(self, walls, doors):
        """Get all blocking rectangles (walls + locked doors)."""
        blockers = list(walls)
        if doors:
            for door in doors:
                if door.blocks_movement():
                    blockers.append(door.get_rect())
        return blockers

    def _check_collision(self, blockers):
        """Check if player collides with any blocker."""
        for blocker in blockers:
            if self.rect.colliderect(blocker):
                return blocker
        return None

    def _try_corner_assist(self, blockers, direction, assist_speed):
        """Try to nudge player around corners. Returns True if assisted."""
        assist_threshold = TILE_SIZE * 0.6  # How close to edge to assist

        if direction in ('left', 'right'):
            # Moving horizontally, try vertical assist
            for blocker in blockers:
                if not self.rect.colliderect(blocker):
                    continue

                # Check if we're near top or bottom edge of the wall
                overlap_top = self.rect.bottom - blocker.top
                overlap_bottom = blocker.bottom - self.rect.top

                if overlap_top > 0 and overlap_top < assist_threshold:
                    # Near top edge - nudge up
                    test_rect = self.rect.copy()
                    test_rect.y -= assist_speed
                    if not any(test_rect.colliderect(b) for b in blockers):
                        self.y -= assist_speed
                        self.rect.y = self.y
                        return True
                elif overlap_bottom > 0 and overlap_bottom < assist_threshold:
                    # Near bottom edge - nudge down
                    test_rect = self.rect.copy()
                    test_rect.y += assist_speed
                    if not any(test_rect.colliderect(b) for b in blockers):
                        self.y += assist_speed
                        self.rect.y = self.y
                        return True
        else:
            # Moving vertically, try horizontal assist
            for blocker in blockers:
                if not self.rect.colliderect(blocker):
                    continue

                # Check if we're near left or right edge of the wall
                overlap_left = self.rect.right - blocker.left
                overlap_right = blocker.right - self.rect.left

                if overlap_left > 0 and overlap_left < assist_threshold:
                    # Near left edge - nudge left
                    test_rect = self.rect.copy()
                    test_rect.x -= assist_speed
                    if not any(test_rect.colliderect(b) for b in blockers):
                        self.x -= assist_speed
                        self.rect.x = self.x
                        return True
                elif overlap_right > 0 and overlap_right < assist_threshold:
                    # Near right edge - nudge right
                    test_rect = self.rect.copy()
                    test_rect.x += assist_speed
                    if not any(test_rect.colliderect(b) for b in blockers):
                        self.x += assist_speed
                        self.rect.x = self.x
                        return True
        return False

    def update(self, keys, walls, doors=None):
        """Update player position based on input and collisions with corner assist."""
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
        assist_speed = current_speed * 0.8  # Corner assist nudge speed

        # Handle movement input (WASD and Arrow keys)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = current_speed

        # Get all blockers
        blockers = self._get_all_blockers(walls, doors)

        # Move horizontally and check collision
        self.x += dx
        self.rect.x = self.x

        collided_h = self._check_collision(blockers)
        if collided_h:
            # Try corner assist first
            direction = 'right' if dx > 0 else 'left'
            if not self._try_corner_assist(blockers, direction, assist_speed):
                # No assist possible, normal collision
                if dx > 0:
                    self.rect.right = collided_h.left
                elif dx < 0:
                    self.rect.left = collided_h.right
                self.x = self.rect.x

        # Move vertically and check collision
        self.y += dy
        self.rect.y = self.y

        collided_v = self._check_collision(blockers)
        if collided_v:
            # Try corner assist first
            direction = 'down' if dy > 0 else 'up'
            if not self._try_corner_assist(blockers, direction, assist_speed):
                # No assist possible, normal collision
                if dy > 0:
                    self.rect.bottom = collided_v.top
                elif dy < 0:
                    self.rect.top = collided_v.bottom
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