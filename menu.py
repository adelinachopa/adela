import pygame
import sys
from setting import *

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_title = pygame.font.Font(None, 74)
        self.font_button = pygame.font.Font(None, 50)

        # Фоновое изображение
        self.background = load_image("image/sprite/main_page.jpg", SCREEN_WIDTH, SCREEN_HEIGHT)

        # Кнопка "Играть" (изображение)
        self.button_rect = pygame.Rect(0, 0, 200, 60)
        self.button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        self.button_color = GREEN
        self.button_hover_color = (0, 200, 0)
        self.button_image = load_image("image/sprite/button_play.jpg", 200, 60)
        # Текст больше не используется
        self.button_text = None
        self.button_text_rect = None

        # Заголовок (оставляем переменные, но не будем рисовать)
        self.title_text = self.font_title.render("Escape to EMK", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rect.collidepoint(event.pos):
                    return "start"
        return None

    def draw(self):
        # Фон
        self.screen.blit(self.background, (0, 0))

        # Кнопка (изображение)
        mouse_pos = pygame.mouse.get_pos()
        # Отрисовываем изображение кнопки
        self.screen.blit(self.button_image, self.button_rect)
        # Если курсор над кнопкой, рисуем белую рамку
        if self.button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, WHITE, self.button_rect, 3)

        pygame.display.flip()

    def run(self):
        while True:
            result = self.handle_events()
            if result is False:  # выход
                return False
            if result == "start":
                return True  # начать игру
            self.draw()
            self.clock.tick(FPS)
