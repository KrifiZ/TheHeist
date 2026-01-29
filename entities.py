# THE HEIST - Entities Module
import pygame
import math
import random
from collections import deque
from settings import (
    TILE_SIZE, GUARD_SPEED, GUARD_CHASE_SPEED, GUARD_VISION_RANGE, GUARD_HEARING_RANGE, GUARD_FOV,
    LASER_CYCLE, DOOR_HOLD_TIME,
    COLOR_GUARD, COLOR_GUARD_ALERT, COLOR_GUARD_SUSPICIOUS, COLOR_DEAD_GUARD,
    COLOR_LASER_ACTIVE, COLOR_LASER_INACTIVE,
    COLOR_DOOR_LOCKED, COLOR_DOOR_UNLOCKED, COLOR_DIAMOND, COLOR_EXIT
)


class Guard:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.alive = True
        
        # AI State
        self.state = 'PATROL'  # PATROL, SUSPICIOUS, CHASE
        self.speed = GUARD_SPEED
        self.direction_vector = pygame.math.Vector2(0, 0)
        self.facing_angle = 0  # Degrees, 0 is right
        
        # Patrol logic
        self.patrol_direction = random.choice(['left', 'right', 'up', 'down'])
        self.change_dir_timer = 0
        
        # Alert logic
        self.suspicion_timer = 0
        self.last_seen_pos = None
        self.alert_timer = 0

        # Pathfinding
        self.current_path = []
        self.path_update_timer = 0

        # Events
        self.triggered_notice = False # For "?" sound
        self.triggered_alert = False  # For "!" sound (if we have one, or just general alert)

    def update(self, walls, player):
        """Update guard AI and movement. Returns 'notice' or 'alert' event string if triggered."""
        if not self.alive:
            return None

        event = None

        # 1. Sensory Check
        can_see_player = self._can_see(player, walls)
        can_hear_player = self._can_hear(player)

        # 2. State Transition Logic
        if can_see_player:
            if self.state == 'PATROL':
                # Grace Period: First sighting triggers Suspicious
                self.state = 'SUSPICIOUS'
                self.suspicion_timer = 60  # 1 second grace period
                self.last_seen_pos = player.get_center()
                event = 'notice'
            elif self.state == 'SUSPICIOUS':
                # If still seeing player while suspicious, tick down grace period
                self.suspicion_timer -= 1
                self.last_seen_pos = player.get_center()
                if self.suspicion_timer <= 0:
                    self.state = 'CHASE'
                    self.alert_timer = 120
                    event = 'alert'
            elif self.state == 'CHASE':
                self.last_seen_pos = player.get_center()
                self.alert_timer = 120

        elif can_hear_player:
            # Hearing noise - investigate and eventually chase
            if self.state == 'PATROL':
                # First time hearing - become suspicious
                self.state = 'SUSPICIOUS'
                self.suspicion_timer = 45  # Shorter timer - will chase soon
                self.last_seen_pos = player.get_center()
                event = 'notice'
            elif self.state == 'SUSPICIOUS':
                # Keep hearing noise - update position and tick down to chase
                self.last_seen_pos = player.get_center()
                self.suspicion_timer -= 1
                if self.suspicion_timer <= 0:
                    # Heard enough noise - start chasing!
                    self.state = 'CHASE'
                    self.alert_timer = 120
                    event = 'alert'

        else:
            # Not seeing or hearing player
            if self.state == 'CHASE':
                # Lost sight, keep chasing for a bit
                self.alert_timer -= 1
                if self.alert_timer <= 0:
                    self.state = 'PATROL'
                    self.current_path = []  # Clear path when returning to patrol
            elif self.state == 'SUSPICIOUS':
                # Lost sight/sound, return to patrol after a bit
                self.suspicion_timer -= 1
                if self.suspicion_timer <= 0:
                    self.state = 'PATROL'
                    self.current_path = []  # Clear path when returning to patrol

        # 3. Action Execution
        if self.state == 'CHASE':
            self._chase_behavior(walls)
        elif self.state == 'SUSPICIOUS':
            self._suspicious_behavior(walls)  # Now takes walls for movement
        else:
            self._patrol_behavior(walls)
            
        return event

    def _find_path(self, walls, target_pos):
        """BFS pathfinding - find path avoiding walls."""
        # Convert positions to grid coordinates
        start_gx = int(self.rect.centerx // TILE_SIZE)
        start_gy = int(self.rect.centery // TILE_SIZE)
        end_gx = int(target_pos[0] // TILE_SIZE)
        end_gy = int(target_pos[1] // TILE_SIZE)

        # Create wall set for fast lookup
        wall_tiles = set()
        for wall in walls:
            wx = wall.x // TILE_SIZE
            wy = wall.y // TILE_SIZE
            wall_tiles.add((wx, wy))

        # BFS
        queue = deque([(start_gx, start_gy, [])])
        visited = {(start_gx, start_gy)}

        while queue:
            gx, gy, path = queue.popleft()

            # Reached target?
            if gx == end_gx and gy == end_gy:
                return path + [(gx, gy)]

            # Check neighbors (4 directions)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = gx + dx, gy + dy

                if (nx, ny) not in visited and (nx, ny) not in wall_tiles:
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(gx, gy)]))

                    # Limit search to avoid lag
                    if len(visited) > 500:
                        return []

        return []  # No path found

    def _follow_path(self, walls, speed):
        """Follow the current path."""
        if not self.current_path:
            return

        # Get next waypoint (grid -> world coordinates)
        next_gx, next_gy = self.current_path[0]
        target_x = next_gx * TILE_SIZE + TILE_SIZE // 2
        target_y = next_gy * TILE_SIZE + TILE_SIZE // 2

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = math.hypot(dx, dy)

        # Reached waypoint? Move to next
        if dist < 5:
            self.current_path.pop(0)
            if not self.current_path:
                return
            next_gx, next_gy = self.current_path[0]
            target_x = next_gx * TILE_SIZE + TILE_SIZE // 2
            target_y = next_gy * TILE_SIZE + TILE_SIZE // 2
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            dist = math.hypot(dx, dy)

        if dist > 0:
            move_x = (dx / dist) * speed
            move_y = (dy / dist) * speed
            self._move(move_x, move_y, walls)
            self.facing_angle = math.degrees(math.atan2(dy, dx))

    def _chase_behavior(self, walls):
        """Move towards last seen position using pathfinding."""
        if not self.last_seen_pos:
            return

        # Update path periodically (every 15 frames)
        self.path_update_timer += 1
        if self.path_update_timer >= 15 or not self.current_path:
            self.path_update_timer = 0
            self.current_path = self._find_path(walls, self.last_seen_pos)

        self._follow_path(walls, GUARD_CHASE_SPEED)

    def _suspicious_behavior(self, walls):
        """Investigate - move slowly towards last heard/seen position using pathfinding."""
        if not self.last_seen_pos:
            return

        # Update path less frequently while investigating
        self.path_update_timer += 1
        if self.path_update_timer >= 30 or not self.current_path:
            self.path_update_timer = 0
            self.current_path = self._find_path(walls, self.last_seen_pos)

        investigate_speed = GUARD_SPEED * 0.7
        self._follow_path(walls, investigate_speed)

    def _patrol_behavior(self, walls):
        """Simple bounce patrol."""
        dx = 0
        dy = 0

        if self.patrol_direction == 'left':
            dx = -GUARD_SPEED
            self.facing_angle = 180
        elif self.patrol_direction == 'right':
            dx = GUARD_SPEED
            self.facing_angle = 0
        elif self.patrol_direction == 'up':
            dy = -GUARD_SPEED
            self.facing_angle = 270
        elif self.patrol_direction == 'down':
            dy = GUARD_SPEED
            self.facing_angle = 90
            
        collision = self._move(dx, dy, walls)
        
        if collision or random.random() < 0.005:
            # Change direction
            possibilities = ['left', 'right', 'up', 'down']
            self.patrol_direction = random.choice(possibilities)

    def _move(self, dx, dy, walls):
        """Move and handle collision. Returns True if collided."""
        collided = False
        
        self.x += dx
        self.rect.x = int(self.x)
        
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0: self.rect.right = wall.left
                if dx < 0: self.rect.left = wall.right
                self.x = self.rect.x
                collided = True
        
        self.y += dy
        self.rect.y = int(self.y)
        
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0: self.rect.bottom = wall.top
                if dy < 0: self.rect.top = wall.bottom
                self.y = self.rect.y
                collided = True
                
        return collided

    def _can_see(self, player, walls):
        """Check line of sight to player with Vision Cone."""
        player_center = player.get_center()
        guard_center = self.rect.center
        
        dx = player_center[0] - guard_center[0]
        dy = player_center[1] - guard_center[1]
        dist = math.hypot(dx, dy)
        
        if dist > GUARD_VISION_RANGE:
            return False
            
        # Check angle
        angle_to_player = math.degrees(math.atan2(dy, dx))
        angle_diff = (angle_to_player - self.facing_angle + 180) % 360 - 180
        
        if abs(angle_diff) > GUARD_FOV / 2:
            return False
            
        # Raycast for walls
        steps = int(dist / (TILE_SIZE / 2))
        for i in range(1, steps + 1): # Check all the way to player
            check_x = guard_center[0] + (dx * i / steps)
            check_y = guard_center[1] + (dy * i / steps)
            check_rect = pygame.Rect(check_x - 1, check_y - 1, 2, 2)
            
            for wall in walls:
                if wall.colliderect(check_rect):
                    return False
                    
        return True

    def _can_hear(self, player):
        """Check if can hear player based on noise radius."""
        noise_radius = player.get_noise_radius()
        if noise_radius == 0:
            return False
            
        player_center = player.get_center()
        guard_center = self.rect.center
        dist = math.hypot(player_center[0] - guard_center[0], player_center[1] - guard_center[1])
        
        # Check if player noise reaches the guard
        return dist < noise_radius

    def draw(self, screen, camera):
        """Draw guard with status and Barks."""
        draw_rect = camera.apply(self.rect)
        
        color = COLOR_GUARD
        if self.state == 'CHASE':
            color = COLOR_GUARD_ALERT
        elif self.state == 'SUSPICIOUS':
            color = COLOR_GUARD_SUSPICIOUS
        
        if not self.alive:
            color = COLOR_DEAD_GUARD
            
        pygame.draw.rect(screen, color, draw_rect)
        
        # Draw eyes/direction
        if self.alive:
            center = draw_rect.center
            end_x = center[0] + math.cos(math.radians(self.facing_angle)) * 15
            end_y = center[1] + math.sin(math.radians(self.facing_angle)) * 15
            pygame.draw.line(screen, (255, 255, 0), center, (end_x, end_y), 2)
            
            # Draw Vision Cone (Debug/Feedback)
            # (Optional, but helps "Vision Cone" feel)
            
            # BARK SYSTEM
            font = pygame.font.Font(None, 36)
            if self.state == 'SUSPICIOUS':
                text = font.render("?", True, (255, 255, 0)) # Yellow ?
                screen.blit(text, (draw_rect.centerx - text.get_width()//2, draw_rect.top - 25))
            elif self.state == 'CHASE':
                text = font.render("!", True, (255, 0, 0))   # Red !
                screen.blit(text, (draw_rect.centerx - text.get_width()//2, draw_rect.top - 25))

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
        """Check if player collects the diamond. Returns True if just collected."""
        if not self.collected and self.rect.colliderect(player.get_rect()):
            self.collected = True
            return True
        return False

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
