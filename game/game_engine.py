import os
import pygame
from .player import Player
from .obstacle import Obstacle

# Game Engine

WHITE = (255, 255, 255)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)

# Speed ceiling (pixels per frame). Keeps long runs fair and stops
# obstacles from moving further per frame than the player is wide.
MAX_SPEED = 14

# Starting values for each difficulty.
# speed = pixels per frame, spawn_interval = frames between obstacles.
DIFFICULTIES = {
    "Easy":   {"speed": 5, "spawn_interval": 90},
    "Medium": {"speed": 6, "spawn_interval": 70},
    "Hard":   {"speed": 8, "spawn_interval": 55},
}

# Keys that choose a difficulty on the selection screen.
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy",   pygame.K_KP1: "Easy",
    pygame.K_2: "Medium", pygame.K_KP2: "Medium",
    pygame.K_3: "Hard",   pygame.K_KP3: "Hard",
}

# The sounds/ folder sits in the project root, one level above this file.
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds")


def load_sound(filename):
    """Load a sound from the sounds/ folder.
    Returns None (instead of crashing) if audio or the file isn't available."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return pygame.mixer.Sound(os.path.join(SOUNDS_DIR, filename))
    except (pygame.error, FileNotFoundError):
        return None


def play_sound(sound):
    """Play a sound if it loaded; otherwise stay silent."""
    if sound is not None:
        sound.play()


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.speed_increase_per_frame = 0.003

        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 60, bold=True)

        # Sound effects (each is None if it couldn't be loaded).
        self.jump_sound = load_sound("jump.wav")
        self.score_sound = load_sound("score.wav")
        self.game_over_sound = load_sound("game_over.wav")

        # First run starts on Medium (same values the game always used).
        self.start_game("Medium")

    def start_game(self, difficulty):
        """Reset all gameplay state and start a fresh run."""
        settings = DIFFICULTIES[difficulty]

        self.difficulty = difficulty
        self.player = Player(80, self.ground_y)

        self.speed = settings["speed"]
        self.spawn_interval = settings["spawn_interval"]  # frames between obstacle spawns
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0

        # "playing" -> "game_over" -> "difficulty" -> back to "playing"
        self.state = "playing"

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "game_over":
            # Enter opens the difficulty menu, Esc exits. Jump keys are ignored.
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "difficulty"
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.state == "difficulty":
            # 1/2/3 starts a new game, Esc exits.
            if event.key in DIFFICULTY_KEYS:
                self.start_game(DIFFICULTY_KEYS[event.key])
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            # Only play the jump sound if the player actually leaves the ground.
            was_on_ground = self.player.on_ground
            self.player.jump()
            if was_on_ground:
                play_sound(self.jump_sound)

    def handle_input(self):
        # Reserved for continuously-held-key input; this runner only
        # needs an edge-triggered jump, handled in handle_event.
        pass

    def update(self):
        # Normal gameplay is frozen on the Game Over and difficulty screens.
        if self.state != "playing":
            return

        # Speed ramps up gradually but never exceeds MAX_SPEED.
        self.speed = min(self.speed + self.speed_increase_per_frame, MAX_SPEED)
        self.player.update()

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(Obstacle(self.width, self.ground_y, self.speed))

        for obstacle in self.obstacles:
            obstacle.move()
            obstacle.speed = self.speed

        # Collision uses each obstacle's swept rect (everything it passed
        # through this frame), so a fast obstacle can never skip over the
        # player's hitbox between two frames.
        player_rect = self.player.rect()
        for obstacle in self.obstacles:
            if obstacle.swept_rect().colliderect(player_rect):
                self.state = "game_over"
                play_sound(self.game_over_sound)
                return

        for obstacle in self.obstacles:
            if not obstacle.scored and obstacle.x + obstacle.width < self.player.x:
                obstacle.scored = True
                self.score += 1
                play_sound(self.score_sound)

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(screen, BROWN, (0, self.ground_y), (self.width, self.ground_y), 4)

        pygame.draw.rect(screen, WHITE, self.player.rect())
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 0))
        screen.blit(score_text, (10, 10))

        if self.state == "game_over":
            self._render_game_over(screen)
        elif self.state == "difficulty":
            self._render_difficulty_menu(screen)

    def _draw_overlay(self, screen):
        # Darken the frozen scene so the text stands out.
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

    def _draw_centered(self, screen, font, text, y):
        surface = font.render(text, True, WHITE)
        screen.blit(surface, surface.get_rect(center=(self.width // 2, y)))

    def _render_game_over(self, screen):
        self._draw_overlay(screen)
        self._draw_centered(screen, self.game_over_font, "GAME OVER", self.height // 2 - 60)
        self._draw_centered(screen, self.font, f"Final Score: {self.score}", self.height // 2 + 5)
        self._draw_centered(screen, self.font, "Press Enter to play again  |  Esc to exit",
                            self.height // 2 + 60)

    def _render_difficulty_menu(self, screen):
        self._draw_overlay(screen)
        self._draw_centered(screen, self.font, "Choose a difficulty", 80)
        self._draw_centered(screen, self.font, "1 - Easy", 140)
        self._draw_centered(screen, self.font, "2 - Medium", 190)
        self._draw_centered(screen, self.font, "3 - Hard", 240)
        self._draw_centered(screen, self.font, "Esc - Exit", 310)