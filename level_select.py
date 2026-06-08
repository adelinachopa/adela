import pygame
import sys
import os
import setting
from setting import *
from save_manager import load_save, get_level_progress

class LevelSelect:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_level = None
        
        # Фоновое изображение
        self.background = load_image("image/sprite/levels_page.jpg", setting.SCREEN_WIDTH, setting.SCREEN_HEIGHT)
        
        # Загружаем прогресс
        self.save_data = load_save()
        
        # Параметры кнопок
        self.button_width = 150
        self.button_height = 150
        self.button_margin = 50
        self.total_buttons = 3
        
        # Вычисляем общую ширину блока кнопок
        total_width = self.total_buttons * self.button_width + (self.total_buttons - 1) * self.button_margin
        start_x = (setting.SCREEN_WIDTH - total_width) // 2
        y = setting.SCREEN_HEIGHT // 2 - self.button_height // 2
        
        # Создаём кнопки
        self.buttons = []
        level_ids = ["level_01", "level_2", "level_3"]
        button_images = ["button_1.jpg", "button_2.jpg", "button_3.jpg"]
        lock_image = "button_lock.jpg"
        
        for i in range(self.total_buttons):
            level_id = level_ids[i]
            button_image = button_images[i]
            rect = pygame.Rect(start_x + i * (self.button_width + self.button_margin), y,
                               self.button_width, self.button_height)
            
            # Проверяем, доступен ли уровень
            unlocked = self.is_level_unlocked(level_id)
            if unlocked:
                image_path = os.path.join("image", "sprite", button_image)
            else:
                image_path = os.path.join("image", "sprite", lock_image)
            
            image = load_image(image_path, self.button_width, self.button_height)
            self.buttons.append({
                "rect": rect,
                "image": image,
                "level_id": level_id,
                "unlocked": unlocked,
                "file": f"levels/{level_id}.json" if level_id != "level_3" else "levels/level_3.json"
            })
    
    def is_level_unlocked(self, level_id):
        """Проверяет, доступен ли уровень на основе прогресса."""
        if level_id == "level_01":
            return True  # Первый уровень всегда доступен
        elif level_id == "level_2":
            # level_2 доступен, если level_01 завершён
            progress = get_level_progress("level_01")
            return progress.get("completed", False)
        elif level_id == "level_3":
            # level_3 доступен, если level_2 завершён
            progress = get_level_progress("level_2")
            return progress.get("completed", False)
        return False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in self.buttons:
                    if btn["rect"].collidepoint(event.pos) and btn["unlocked"]:
                        self.selected_level = btn["file"]
                        return "play"
        return None
    
    def draw(self):
        # Фон
        self.screen.blit(self.background, (0, 0))
        
        # Рисуем кнопки
        for btn in self.buttons:
            self.screen.blit(btn["image"], btn["rect"])
            # Если заблокирована, можно добавить затемнение
            if not btn["unlocked"]:
                s = pygame.Surface((self.button_width, self.button_height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128))  # полупрозрачный чёрный
                self.screen.blit(s, btn["rect"])
        
        # Подписи уровней (опционально)
        font = pygame.font.Font(None, 36)
        for i, btn in enumerate(self.buttons):
            text = f"Уровень {i+1}"
            text_surface = font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(btn["rect"].centerx, btn["rect"].bottom + 20))
            self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Запускает экран выбора уровней. Возвращает путь к файлу уровня или None для выхода."""
        while True:
            result = self.handle_events()
            if result is False:  # выход из игры
                return None
            if result == "back":  # вернуться в меню
                return "back"
            if result == "play":  # выбран уровень
                return self.selected_level
            self.draw()
            self.clock.tick(FPS)