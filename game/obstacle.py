import math
import pygame

class Obstacle:
    def __init__(self, x, ground_y, speed, width=25, height=40):
        self.x = x
        self.prev_x = x  # position before the most recent move
        self.width = width
        self.height = height
        self.y = ground_y - height
        self.speed = speed
        self.scored = False

    def move(self):
        self.prev_x = self.x
        self.x -= self.speed

    def off_screen(self):
        return self.x + self.width < 0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def swept_rect(self):
        """Rect covering the whole area the obstacle passed through this
        frame (from prev_x to x). Used for collision so that a fast
        obstacle can't skip over the player between two frames."""
        left = math.floor(self.x)
        right = math.ceil(self.prev_x + self.width)
        return pygame.Rect(left, self.y, right - left, self.height)