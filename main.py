# THE HEIST - STEALTH PROTOCOL
# Main Game Module
import pygame
import math
import os
import json
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ATTACK_RANGE,
    COLOR_BG, COLOR_HUD_TEXT, COLOR_HUD_BG,
    STATE_INTRO, STATE_MENU, STATE_PLAYING, STATE_WIN, STATE_LOSE, STATE_LEVEL_COMPLETE,
    LEVELS, SAVE_FILE
)
from player import Player
from camera import Camera
from level import Level
from entities import Guard, Laser, Door, Diamond, Exit


# Star Wars style intro text
INTRO_TEXT = """THE HEIST
STEALTH PROTOCOL

It is a time of greed and absolute control.
The IRONCLAD HOLDINGS corporation has amassed
wealth exceeding the budgets of superpowers,
hoarding it within their unbreachable fortress.
They claim their vault is impenetrable.

But they don't know YOU.

You are "THE GHOST" - the undisputed king
of thieves. For you, high-tech security is
just a suggestion, and guards are merely
obstacles to be removed.

Your target is the "HEART OF THE LEVIATHAN",
a priceless diamond hidden deep in the
lion's den.

The lasers are armed.
The guards have orders to kill on sight.

It is time to vanish into the shadows
and prove that there is no lock
you cannot pick..."""


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("THE HEIST - STEALTH PROTOCOL")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.intro_font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 48)
        self.running = True
        self.current_level_index = 0
        self.game_state = STATE_INTRO

        # Intro scrolling
        self.intro_y = SCREEN_HEIGHT
        self.intro_speed = 0.8
        self.intro_static_text = "Somewhere in the shadows of the global elite..."
        self.intro_static_timer = 0
        self.intro_static_duration = 3000  # 3 seconds for static text
        self.intro_phase = 'static'  # 'static' or 'scroll'

        # Menu selection
        self.menu_selection = 0  # 0 = New Game, 1 = Continue
        self.has_save = self._check_save_exists()

        # Load Sounds
        self.sounds = {}
        self._load_sounds()

        # Play background music
        if 'music' in self.sounds:
            pygame.mixer.music.load(os.path.join('sounds', 'main_audio.mp3'))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)

    # ==================== SAVE SYSTEM ====================

    def _check_save_exists(self):
        """Check if a save file exists."""
        return os.path.exists(SAVE_FILE)

    def _save_game(self):
        """Save current progress to file."""
        save_data = {
            'level': self.current_level_index,
            'max_level': self.current_level_index
        }
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f)
        except Exception as e:
            print(f"Warning: Could not save game: {e}")

    def _load_game(self):
        """Load progress from save file."""
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
                self.current_level_index = save_data.get('level', 0)
                return True
        except Exception as e:
            print(f"Warning: Could not load save: {e}")
            return False

    def _delete_save(self):
        """Delete the save file for new game."""
        if os.path.exists(SAVE_FILE):
            try:
                os.remove(SAVE_FILE)
            except Exception:
                pass

    # ==================== SOUNDS ====================

    def _load_sounds(self):
        """Load all game sounds."""
        sound_files = {
            'collect': 'collect_diamond.mp3',
            'laser_death': 'game_laser_shot.mp3',
            'level_complete': 'game_level_complete.mp3',
            'game_over': 'game_over.mp3',
            'guard_notice': 'guard_notice_sound.mp3',
            'music': 'main_audio.mp3'
        }

        for name, filename in sound_files.items():
            path = os.path.join('sounds', filename)
            if os.path.exists(path):
                if name == 'music':
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

    # ==================== LEVEL MANAGEMENT ====================

    def _init_level(self):
        """Initialize or reset the level and all entities."""
        self.level = Level(LEVELS[self.current_level_index])
        self.camera = Camera()
        spawns = self.level.get_spawn_points()

        if spawns['player']:
            self.player = Player(*spawns['player'])
            self.player_spawn = spawns['player']
        else:
            self.player = Player(60, 60)
            self.player_spawn = (60, 60)

        self.guards = []
        for pos in spawns['guards']:
            self.guards.append(Guard(*pos))

        self.lasers = []
        for pos in spawns['lasers']:
            self.lasers.append(Laser(*pos))

        self.doors = []
        for pos in spawns['doors']:
            self.doors.append(Door(*pos))

        if spawns['diamond']:
            self.diamond = Diamond(*spawns['diamond'])
        else:
            self.diamond = Diamond(800, 700)

        if spawns['exit']:
            self.exit = Exit(*spawns['exit'])
        else:
            self.exit = Exit(1140, 840)

        self.game_state = STATE_PLAYING
        self.door_progress = 0

    def _reset_game(self):
        """Reset the game to initial state."""
        self._init_level()

    # ==================== EVENT HANDLING ====================

    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                # Intro - skip on any key
                if self.game_state == STATE_INTRO:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                        self.game_state = STATE_MENU

                # Menu controls
                elif self.game_state == STATE_MENU:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.menu_selection = 0
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        if self.has_save:
                            self.menu_selection = 1
                    elif event.key == pygame.K_RETURN:
                        if self.menu_selection == 0:
                            # New Game
                            self._delete_save()
                            self.current_level_index = 0
                            self._init_level()
                        else:
                            # Continue
                            if self._load_game():
                                self._init_level()
                            else:
                                self.current_level_index = 0
                                self._init_level()

                # Restart on R or ENTER when game over
                elif self.game_state in [STATE_LOSE, STATE_WIN]:
                    if event.key == pygame.K_r or event.key == pygame.K_RETURN:
                        self.current_level_index = 0
                        self._init_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = STATE_MENU
                        self.has_save = self._check_save_exists()

                elif self.game_state == STATE_LEVEL_COMPLETE:
                    if event.key == pygame.K_RETURN:
                        self.current_level_index += 1
                        self._save_game()  # Save progress
                        if self.current_level_index >= len(LEVELS):
                            self.game_state = STATE_WIN
                            self._play_sound('level_complete')
                        else:
                            self._init_level()

                # Attack (takedown) on X key
                elif event.key == pygame.K_x and self.game_state == STATE_PLAYING:
                    self._handle_attack()

                # ESC to menu during gameplay
                elif event.key == pygame.K_ESCAPE and self.game_state == STATE_PLAYING:
                    self._save_game()
                    self.game_state = STATE_MENU
                    self.has_save = self._check_save_exists()

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

    # ==================== UPDATE ====================

    def _update(self, dt):
        """Update game state."""
        # Update intro
        if self.game_state == STATE_INTRO:
            self._update_intro(dt)
            return

        if self.game_state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()

        self.player.update(keys, self.level.get_walls(), self.doors)
        self.camera.update(self.player)

        for guard in self.guards:
            event = guard.update(self.level.get_walls(), self.player)
            if event == 'alert':
                self._play_sound('guard_notice')

        for laser in self.lasers:
            laser.update(dt)

        holding_space = keys[pygame.K_SPACE]
        for door in self.doors:
            progress = door.update(self.player, holding_space, dt)
            if progress > 0:
                self.door_progress = progress

        if not holding_space:
            self.door_progress = max(0, self.door_progress - dt / 500)

        if self.diamond.update(self.player):
            self._play_sound('collect')

        self._check_collisions()

        if self.exit.check_win(self.player, self.diamond):
            if self.current_level_index < len(LEVELS) - 1:
                self.game_state = STATE_LEVEL_COMPLETE
                self._play_sound('level_complete')
            else:
                self.game_state = STATE_WIN
                self._play_sound('level_complete')

    def _update_intro(self, dt):
        """Update intro animation."""
        if self.intro_phase == 'static':
            self.intro_static_timer += dt
            if self.intro_static_timer >= self.intro_static_duration:
                self.intro_phase = 'scroll'
        else:
            self.intro_y -= self.intro_speed
            # End intro when text is fully scrolled
            lines = INTRO_TEXT.split('\n')
            text_height = len(lines) * 30
            if self.intro_y < -text_height - 100:
                self.game_state = STATE_MENU

    def _check_collisions(self):
        """Check for deadly collisions."""
        player_rect = self.player.get_rect()

        for guard in self.guards:
            if guard.is_alive() and player_rect.colliderect(guard.get_rect()):
                self.game_state = STATE_LOSE
                self._play_sound('game_over')
                return

        for laser in self.lasers:
            if laser.is_dangerous() and player_rect.colliderect(laser.get_rect()):
                self.game_state = STATE_LOSE
                self._play_sound('laser_death')
                self._play_sound('game_over')
                return

    # ==================== DRAWING ====================

    def _draw(self):
        """Draw everything."""
        if self.game_state == STATE_INTRO:
            self._draw_intro()
            pygame.display.flip()
            return

        if self.game_state == STATE_MENU:
            self._draw_menu()
            pygame.display.flip()
            return

        self.screen.fill(COLOR_BG)
        self.level.draw(self.screen, self.camera)

        for laser in self.lasers:
            laser.draw(self.screen, self.camera)

        for door in self.doors:
            door.draw(self.screen, self.camera)

        self.diamond.draw(self.screen, self.camera)
        self.exit.draw(self.screen, self.camera, self.diamond.is_collected())

        for guard in self.guards:
            guard.draw(self.screen, self.camera)

        self.player.draw(self.screen, self.camera)
        self._draw_hud()

        if self.game_state == STATE_WIN:
            self._draw_overlay("ALL LEVELS COMPLETED!", (0, 255, 0), "Press ENTER to restart | ESC for menu")
        elif self.game_state == STATE_LOSE:
            self._draw_overlay("GAME OVER", (255, 0, 0), "Press ENTER to restart | ESC for menu")
        elif self.game_state == STATE_LEVEL_COMPLETE:
            self._draw_overlay("LEVEL COMPLETE", (0, 255, 0), "Press ENTER for next level")

        pygame.display.flip()

    def _draw_intro(self):
        """Draw Star Wars style intro."""
        self.screen.fill((0, 0, 0))

        if self.intro_phase == 'static':
            # Draw static text with fade in
            alpha = min(255, int(self.intro_static_timer / 10))
            text = self.intro_font.render(self.intro_static_text, True, (100, 100, 255))
            text.set_alpha(alpha)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
        else:
            # Draw scrolling text with perspective effect
            lines = INTRO_TEXT.split('\n')

            for i, line in enumerate(lines):
                y_pos = self.intro_y + i * 30

                # Only draw if on screen
                if y_pos < -30 or y_pos > SCREEN_HEIGHT + 30:
                    continue

                # Perspective effect - text gets smaller/dimmer as it goes up
                perspective = 1.0 - (SCREEN_HEIGHT / 2 - y_pos) / SCREEN_HEIGHT
                perspective = max(0.3, min(1.0, perspective))

                # Color fades to yellow at top
                color_val = int(255 * perspective)
                if y_pos < SCREEN_HEIGHT / 3:
                    color = (255, 255, int(100 * perspective))  # Yellow tint
                else:
                    color = (color_val, color_val, int(color_val * 0.5))  # Gold

                # Title gets special treatment
                if line == "THE HEIST" or line == "STEALTH PROTOCOL":
                    text = self.title_font.render(line, True, (255, 255, 0))
                else:
                    text = self.intro_font.render(line, True, color)

                rect = text.get_rect(center=(SCREEN_WIDTH // 2, int(y_pos)))
                self.screen.blit(text, rect)

        # Skip hint
        skip_text = self.small_font.render("Press ENTER to skip", True, (80, 80, 80))
        self.screen.blit(skip_text, (10, SCREEN_HEIGHT - 30))

    def _draw_menu(self):
        """Draw main menu with save options."""
        self.screen.fill(COLOR_BG)

        # Title
        title = self.title_font.render("THE HEIST", True, (255, 255, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)

        subtitle = self.font.render("STEALTH PROTOCOL", True, (200, 200, 0))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(subtitle, subtitle_rect)

        # Menu options
        menu_y = SCREEN_HEIGHT // 2 - 20

        # New Game option
        new_game_color = (255, 255, 255) if self.menu_selection == 0 else (100, 100, 100)
        new_game_text = "> NEW GAME <" if self.menu_selection == 0 else "  NEW GAME  "
        new_game = self.font.render(new_game_text, True, new_game_color)
        new_game_rect = new_game.get_rect(center=(SCREEN_WIDTH // 2, menu_y))
        self.screen.blit(new_game, new_game_rect)

        # Continue option (only if save exists)
        if self.has_save:
            continue_color = (255, 255, 255) if self.menu_selection == 1 else (100, 100, 100)
            continue_text = "> CONTINUE <" if self.menu_selection == 1 else "  CONTINUE  "
            continue_opt = self.font.render(continue_text, True, continue_color)
            continue_rect = continue_opt.get_rect(center=(SCREEN_WIDTH // 2, menu_y + 50))
            self.screen.blit(continue_opt, continue_rect)

        # Controls
        controls = [
            "Controls:",
            "WASD / Arrows: Move (Silent)",
            "SHIFT + Move: RUN (LOUD! Guards WILL hear you!)",
            "X: Takedown (sneak behind guards)",
            "SPACE (hold): Unlock Door",
            "ESC: Pause / Menu"
        ]

        for i, line in enumerate(controls):
            text = self.small_font.render(line, True, (100, 100, 100))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100 + i * 22))
            self.screen.blit(text, rect)

    def _draw_hud(self):
        """Draw minimal HUD."""
        # Level indicator
        level_text = f"LEVEL {self.current_level_index + 1}/{len(LEVELS)}"
        level_surface = self.small_font.render(level_text, True, (150, 150, 150))
        self.screen.blit(level_surface, (SCREEN_WIDTH // 2 - 40, 10))

        # Diamond status
        diamond_text = "DIAMOND: COLLECTED" if self.diamond.is_collected() else "DIAMOND: NOT COLLECTED"
        diamond_color = (0, 255, 255) if self.diamond.is_collected() else (150, 150, 150)
        text_surface = self.small_font.render(diamond_text, True, diamond_color)
        self.screen.blit(text_surface, (10, 10))

        # Running warning
        if self.player.get_noise_radius() > 0:
            pulse = abs(pygame.time.get_ticks() % 500 - 250) / 250
            red_intensity = int(150 + 105 * pulse)
            warning_color = (red_intensity, 50, 50)

            warning_rect = pygame.Rect(SCREEN_WIDTH - 220, 10, 210, 50)
            pygame.draw.rect(self.screen, warning_color, warning_rect)
            pygame.draw.rect(self.screen, (255, 100, 100), warning_rect, 3)

            warning_text = self.font.render("!! RUNNING !!", True, (255, 255, 255))
            self.screen.blit(warning_text, (SCREEN_WIDTH - 205, 15))

            noise_text = self.small_font.render("Guards can HEAR you!", True, (255, 200, 200))
            self.screen.blit(noise_text, (SCREEN_WIDTH - 200, 38))
        else:
            stealth_text = self.small_font.render("SILENT", True, (100, 200, 100))
            self.screen.blit(stealth_text, (SCREEN_WIDTH - 60, 15))

        # Door progress
        if self.door_progress > 0:
            bar_width = 150
            bar_height = 15
            bar_x = 10
            bar_y = 35

            pygame.draw.rect(self.screen, COLOR_HUD_BG, (bar_x, bar_y, bar_width, bar_height))
            progress_width = int(bar_width * min(self.door_progress, 1.0))
            pygame.draw.rect(self.screen, (139, 69, 19), (bar_x, bar_y, progress_width, bar_height))
            pygame.draw.rect(self.screen, COLOR_HUD_TEXT, (bar_x, bar_y, bar_width, bar_height), 1)
            label = self.small_font.render("UNLOCKING...", True, COLOR_HUD_TEXT)
            self.screen.blit(label, (bar_x + bar_width + 10, bar_y - 2))

        # Controls hint
        controls = "WASD: Move | SHIFT: Run (LOUD!) | X: Takedown | SPACE: Unlock | ESC: Menu"
        controls_surface = self.small_font.render(controls, True, (100, 100, 100))
        self.screen.blit(controls_surface, (10, SCREEN_HEIGHT - 25))

    def _draw_overlay(self, text, color, subtext="Press R or ENTER to restart"):
        """Draw game over/win overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(text_surface, text_rect)

        restart_surface = self.small_font.render(subtext, True, COLOR_HUD_TEXT)
        restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(restart_surface, restart_rect)

    # ==================== MAIN LOOP ====================

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
