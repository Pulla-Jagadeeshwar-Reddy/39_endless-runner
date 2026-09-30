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

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.player = Player(80, self.ground_y)

        self.speed = 6
        self.speed_increase_per_frame = 0.003

        self.spawn_interval = 70  # frames between obstacle spawns
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.game_over = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.game_over:
            # Game Over screen: ignore jump keys, wait for Enter or Esc.
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            self.player.jump()

    def handle_input(self):
        # Reserved for continuously-held-key input; this runner only
        # needs an edge-triggered jump, handled in handle_event.
        pass

    def update(self):
        # Normal gameplay is frozen while the Game Over screen is showing.
        if self.game_over:
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
                self.game_over = True
                return

        for obstacle in self.obstacles:
            if not obstacle.scored and obstacle.x + obstacle.width < self.player.x:
                obstacle.scored = True
                self.score += 1

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(screen, BROWN, (0, self.ground_y), (self.width, self.ground_y), 4)

        pygame.draw.rect(screen, WHITE, self.player.rect())
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 0))
        screen.blit(score_text, (10, 10))

        if self.game_over:
            self._render_game_over(screen)

    def _render_game_over(self, screen):
        # Darken the frozen scene so the text stands out.
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        center_x = self.width // 2

        title = self.game_over_font.render("GAME OVER", True, WHITE)
        screen.blit(title, title.get_rect(center=(center_x, self.height // 2 - 60)))

        final_score = self.font.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(final_score, final_score.get_rect(center=(center_x, self.height // 2 + 5)))

        prompt = self.font.render("Press Enter or Esc to exit", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(center_x, self.height // 2 + 60)))