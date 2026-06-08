# создание стен и пратформ и создание логики уровней
import pygame
from setting import *


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, image_path, color=None):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if image_path:
            try:
                # Используем find_image_file для регистронезависимого поиска
                from setting import find_image_file
                actual_path = find_image_file(image_path)
                tile = pygame.image.load(actual_path)
                tile_w, tile_h = tile.get_size()
                # Тайлинг: повторяем текстуру по всей поверхности
                for i in range(0, width, tile_w):
                    for j in range(0, height, tile_h):
                        self.image.blit(tile, (i, j))
            except (FileNotFoundError, pygame.error) as e:
                # Логируем ошибку
                error_msg = f"Warning: Could not load platform texture '{image_path}'. Error: {e}"
                print(error_msg)
                
                # Пишем в лог
                from datetime import datetime
                try:
                    with open("game_errors.log", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now()}] {error_msg}\n")
                except:
                    pass
                
                # Заливка цветом при ошибке
                if color:
                    self.image.fill(color)
                else:
                    self.image.fill(GREEN)
        else:
            if color:
                self.image.fill(color)
            else:
                self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))
