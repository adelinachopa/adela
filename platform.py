# создание стен и пратформ и создание логики уровней
import pygame
from setting import *


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, image_path, color=None):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if image_path:
            try:
                tile = pygame.image.load(image_path).convert_alpha()
                tile_w, tile_h = tile.get_size()
                # Заполняем поверхность тайлами
                for i in range(0, width, tile_w):
                    for j in range(0, height, tile_h):
                        self.image.blit(tile, (i, j))
            except (FileNotFoundError, pygame.error) as e:
                # Логирование ошибки
                error_msg = f"Warning: Could not load platform texture '{image_path}'. Error: {e}"
                print(error_msg)
                
                # Запись в лог файл
                from datetime import datetime
                try:
                    with open("game_errors.log", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now()}] {error_msg}\n")
                except:
                    pass  # Если не удалось записать в лог, продолжаем
                
                # Используем цвет вместо текстуры
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