# THE HEIST - STEALTH PROTOCOL
# Main Game Module
import pygame
import math
import os
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ATTACK_RANGE,
    COLOR_BG, COLOR_HUD_TEXT, COLOR_HUD_BG,
    STATE_MENU, STATE_PLAYING, STATE_WIN, STATE_LOSE, STATE_LEVEL_COMPLETE,
    LEVELS
)
from player import Player
from camera import Camera
from level import Level
from entities import Guard, Laser, Door, Diamond, Exit


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("THE HEIST - STEALTH PROTOCOL")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.running = True
        self.current_level_index = 0
        self.game_state = STATE_MENU
        
        # Load Sounds
        self.sounds = {}
        self._load_sounds()
        
        # Play background music
        if 'music' in self.sounds:
            pygame.mixer.music.load(os.path.join('sounds', 'main_audio.mp3'))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1) # Loop forever

    def _load_sounds(self):
        """Load all game sounds."""
        sound_files = {
            'collect': 'collect_diamond.mp3',
            'laser_death': 'game_laser_shot.mp3',
            'level_complete': 'game_level_complete.mp3',
            'game_over': 'game_over.mp3',
            'guard_notice': 'guard_notice_sound.mp4', # Might fail if MP4 is video-only container
            'music': 'main_audio.mp3'
        }
        
        for name, filename in sound_files.items():
            path = os.path.join('sounds', filename)
            if os.path.exists(path):
                if name == 'music':
                    # Music is streamed, not loaded as Sound object
                    self.sounds['music'] = path
                else:
                    try:
                        self.sounds[name] = pygame.mixer.Sound(path)
                    except pygame.error as e:
                        print(f"Warning: Could not load sound {filename}: {e}")
            else:
                print(f"Warning: Sound file not found: {path}")

    def _play_sound(self, name):
        """Play a sound if it exists."""
        if name in self.sounds:
            self.sounds[name].play()

    def _init_level(self):
        """Initialize or reset the level and all entities."""
        self.level = Level(LEVELS[self.current_level_index])
        self.camera = Camera()
        spawns = self.level.get_spawn_points()

        # Create player
        if spawns['player']:
            self.player = Player(*spawns['player'])
            self.player_spawn = spawns['player']
        else:
            self.player = Player(60, 60)
            self.player_spawn = (60, 60)

        # Create guards
        self.guards = []
        for pos in spawns['guards']:
            self.guards.append(Guard(*pos))

        # Create lasers
        self.lasers = []
        for pos in spawns['lasers']:
            self.lasers.append(Laser(*pos))

        # Create doors
        self.doors = []
        for pos in spawns['doors']:
            self.doors.append(Door(*pos))

        # Create diamond
        if spawns['diamond']:
            self.diamond = Diamond(*spawns['diamond'])
        else:
            self.diamond = Diamond(800, 700)

        # Create exit
        if spawns['exit']:
            self.exit = Exit(*spawns['exit'])
        else:
            self.exit = Exit(1140, 840)

        # Reset game state
        self.game_state = STATE_PLAYING
        self.door_progress = 0

    def _reset_game(self):
        """Reset the game to initial state."""
        self._init_level()

    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                # Menu controls
                if self.game_state == STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        self.current_level_index = 0
                        self._init_level()
                        self.game_state = STATE_PLAYING
                
                # Restart on R or ENTER when game over
                elif self.game_state in [STATE_LOSE, STATE_WIN]:
                    if event.key == pygame.K_r or event.key == pygame.K_RETURN:
                        self.current_level_index = 0
                        self._init_level()
                        self.game_state = STATE_PLAYING
                        
                elif self.game_state == STATE_LEVEL_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.current_level_index += 1
                        if self.current_level_index >= len(LEVELS):
                            self.game_state = STATE_WIN
                            self._play_sound('level_complete') # Or win sound if separate
                        else:
                            self._init_level()
                            self.game_state = STATE_PLAYING

                # Attack (takedown) on X key
                elif event.key == pygame.K_x and self.game_state == STATE_PLAYING:
                    self._handle_attack()

    def _handle_attack(self):
        """Handle player attack - kill nearby guards."""
        player_center = self.player.get_center()

        for guard in self.guards:
            if guard.is_alive():
                guard_center = guard.get_center()
                distance = math.sqrt(
                    (player_center[0] - guard_center[0]) ** 2 +
                    (player_center[1] - guard_center[1]) ** 2
                )
                if distance < ATTACK_RANGE:
                    guard.kill()

    def _update(self, dt):
        """Update game state."""
        if self.game_state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()

        # Update player
        self.player.update(keys, self.level.get_walls(), self.doors)

        # Update camera
        self.camera.update(self.player)

        # Update guards
        for guard in self.guards:
            event = guard.update(self.level.get_walls(), self.player)
            if event == 'notice':
                self._play_sound('guard_notice')
            elif event == 'alert':
                # Can play a sharper alert sound if available, reusing notice for now or adding another
                self._play_sound('guard_notice') 

        # Update lasers
        for laser in self.lasers:
            laser.update(dt)

        # Update doors
        holding_space = keys[pygame.K_SPACE]
        for door in self.doors:
            progress = door.update(self.player, holding_space, dt)
            if progress > 0:
                self.door_progress = progress

        # If no door is being unlocked, decay progress display
        if not holding_space:
            self.door_progress = max(0, self.door_progress - dt / 500)

        # Update diamond
        if self.diamond.update(self.player):
            self._play_sound('collect')

        # Check collisions
        self._check_collisions()

        # Check win condition
        if self.exit.check_win(self.player, self.diamond):
            if self.current_level_index < len(LEVELS) - 1:
                self.game_state = STATE_LEVEL_COMPLETE
                self._play_sound('level_complete')
            else:
                self.game_state = STATE_WIN
                self._play_sound('level_complete') # Reusing complete sound for win

    def _check_collisions(self):
        """Check for deadly collisions."""
        player_rect = self.player.get_rect()

        # Check guard collision
        for guard in self.guards:
            if guard.is_alive() and player_rect.colliderect(guard.get_rect()):
                self.game_state = STATE_LOSE
                self._play_sound('game_over')
                return

        # Check laser collision
        for laser in self.lasers:
            if laser.is_dangerous() and player_rect.colliderect(laser.get_rect()):
                self.game_state = STATE_LOSE
                self._play_sound('laser_death')
                self._play_sound('game_over')
                return

    def _draw(self):
        """Draw everything."""
        if self.game_state == STATE_MENU:
            self._draw_menu()
            pygame.display.flip()
            return

        # Clear screen
        self.screen.fill(COLOR_BG)

        # Draw level (walls)
        self.level.draw(self.screen, self.camera)

        # Draw entities
        for laser in self.lasers:
            laser.draw(self.screen, self.camera)

        for door in self.doors:
            door.draw(self.screen, self.camera)

        self.diamond.draw(self.screen, self.camera)
        self.exit.draw(self.screen, self.camera, self.diamond.is_collected())

        for guard in self.guards:
            guard.draw(self.screen, self.camera)

        # Draw player
        self.player.draw(self.screen, self.camera)

        # Draw HUD
        self._draw_hud()

        # Draw game state overlay
        if self.game_state == STATE_WIN:
            self._draw_overlay("ALL LEVELS COMPLETED!", (0, 255, 0))
        elif self.game_state == STATE_LOSE:
            self._draw_overlay("GAME OVER", (255, 0, 0))
        elif self.game_state == STATE_LEVEL_COMPLETE:
            self._draw_overlay("LEVEL COMPLETE", (0, 255, 0), "Press ENTER for next level")

        pygame.display.flip()

    def _draw_menu(self):
        """Draw main menu."""
        self.screen.fill(COLOR_BG)
        title = self.font.render("THE HEIST - STEALTH PROTOCOL", True, (255, 255, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title, title_rect)

        start_text = self.small_font.render("Press ENTER to Start", True, (255, 255, 255))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(start_text, start_rect)
        
        controls = [
            "Controls:",
            "WASD / Arrows: Move (Silent)",
            "SHIFT: Run (Loud)",
            "X: Takedown",
            "SPACE (hold): Unlock Door"
        ]
        
        for i, line in enumerate(controls):
            text = self.small_font.render(line, True, (150, 150, 150))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80 + i * 25))
            self.screen.blit(text, rect)

    def _draw_hud(self):
        """Draw minimal HUD."""
        # Diamond status
        diamond_text = "DIAMOND: COLLECTED" if self.diamond.is_collected() else "DIAMOND: NOT COLLECTED"
        diamond_color = (0, 255, 255) if self.diamond.is_collected() else (150, 150, 150)
        text_surface = self.small_font.render(diamond_text, True, diamond_color)
        self.screen.blit(text_surface, (10, 10))

        # Door unlock progress bar (only show when unlocking)
        if self.door_progress > 0:
            bar_width = 150
            bar_height = 15
            bar_x = 10
            bar_y = 35

            # Background
            pygame.draw.rect(self.screen, COLOR_HUD_BG, (bar_x, bar_y, bar_width, bar_height))
            # Progress
            progress_width = int(bar_width * min(self.door_progress, 1.0))
            pygame.draw.rect(self.screen, (139, 69, 19), (bar_x, bar_y, progress_width, bar_height))
            # Border
            pygame.draw.rect(self.screen, COLOR_HUD_TEXT, (bar_x, bar_y, bar_width, bar_height), 1)
            # Label
            label = self.small_font.render("UNLOCKING...", True, COLOR_HUD_TEXT)
            self.screen.blit(label, (bar_x + bar_width + 10, bar_y - 2))

        # Controls hint
        controls = "WASD: Move | SHIFT: Run | X: Takedown | SPACE: Unlock Door"
        controls_surface = self.small_font.render(controls, True, (100, 100, 100))
        self.screen.blit(controls_surface, (10, SCREEN_HEIGHT - 25))

    def _draw_overlay(self, text, color, subtext="Press R or ENTER to restart"):
        """Draw game over/win overlay."""
        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # Main text
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(text_surface, text_rect)

        # Restart instruction
        restart_surface = self.small_font.render(subtext, True, COLOR_HUD_TEXT)
        restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(restart_surface, restart_rect)

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS)

            self._handle_events()
            self._update(dt)
            self._draw()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()