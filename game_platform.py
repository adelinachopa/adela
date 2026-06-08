# создание стен и пратформ и создание логики уровней
import pygame
from setting import *


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, image_path, color=None):
        super().__init__()
        if image_path:
            # Используем load_image() из setting.py для регистронезависимой загрузки
            self.image = load_image(image_path, width, height, color or GREEN)
        else:
            self.image = pygame.Surface((width, height))
            if color:
                self.image.fill(color)
            else:
                self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))
