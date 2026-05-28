"""
Модуль джойстика для мобильного управления в игре Escape to EMK.
Реализует виртуальные джойстики для управления персонажами на сенсорных экранах.
"""

import pygame
from setting import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, RED

class VirtualJoystick:
    """Виртуальный джойстик для сенсорного управления"""
    
    def __init__(self, x, y, radius=80, inner_radius=30, color=(100, 100, 100, 150)):
        """
        Инициализирует виртуальный джойстик.
        
        Args:
            x, y: Центральная позиция джойстика
            radius: Внешний радиус джойстика
            inner_radius: Радиус внутреннего круга (ручки)
            color: Цвет джойстика (RGBA)
        """
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.inner_radius = inner_radius
        self.color = color
        
        # Текущая позиция ручки (относительно центра)
        self.handle_x = 0
        self.handle_y = 0
        
        # Активен ли джойстик
        self.active = False
        
        # ID касания, управляющего этим джойстиком
        self.touch_id = None
        
        # Создаем поверхности для отрисовки
        self.create_surfaces()
    
    def create_surfaces(self):
        """Создает поверхности для отрисовки джойстика"""
        # Внешний круг (фон)
        self.outer_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.outer_surface, (*self.color[:3], 100), 
                          (self.radius, self.radius), self.radius)
        
        # Внутренний круг (ручка)
        self.inner_surface = pygame.Surface((self.inner_radius * 2, self.inner_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.inner_surface, (*self.color[:3], 200), 
                          (self.inner_radius, self.inner_radius), self.inner_radius)
    
    def handle_event(self, event):
        """
        Обрабатывает события касаний/мыши.
        
        Returns:
            bool: True если событие обработано этим джойстиком
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Для тестирования на ПК
            mouse_x, mouse_y = pygame.mouse.get_pos()
            distance = ((mouse_x - self.center_x) ** 2 + (mouse_y - self.center_y) ** 2) ** 0.5
            
            if distance <= self.radius:
                self.active = True
                self.update_handle_position(mouse_x, mouse_y)
                return True
        
        elif event.type == pygame.MOUSEMOTION and self.active:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.update_handle_position(mouse_x, mouse_y)
            return True
        
        elif event.type == pygame.MOUSEBUTTONUP and self.active:
            self.reset()
            return True
        
        # Обработка сенсорных событий (для мобильных устройств)
        elif event.type == pygame.FINGERDOWN:
            touch_x = event.x * SCREEN_WIDTH
            touch_y = event.y * SCREEN_HEIGHT
            distance = ((touch_x - self.center_x) ** 2 + (touch_y - self.center_y) ** 2) ** 0.5
            
            if distance <= self.radius and self.touch_id is None:
                self.touch_id = event.finger_id
                self.active = True
                self.update_handle_position(touch_x, touch_y)
                return True
        
        elif event.type == pygame.FINGERMOTION and self.active and event.finger_id == self.touch_id:
            touch_x = event.x * SCREEN_WIDTH
            touch_y = event.y * SCREEN_HEIGHT
            self.update_handle_position(touch_x, touch_y)
            return True
        
        elif event.type == pygame.FINGERUP and self.active and event.finger_id == self.touch_id:
            self.reset()
            return True
        
        return False
    
    def update_handle_position(self, x, y):
        """Обновляет позицию ручки джойстика"""
        # Вычисляем вектор от центра к точке касания
        dx = x - self.center_x
        dy = y - self.center_y
        
        # Ограничиваем длину вектора радиусом джойстика
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > self.radius:
            dx = dx * self.radius / distance
            dy = dy * self.radius / distance
        
        self.handle_x = dx
        self.handle_y = dy
    
    def reset(self):
        """Сбрасывает джойстик в исходное состояние"""
        self.handle_x = 0
        self.handle_y = 0
        self.active = False
        self.touch_id = None
    
    def get_direction(self):
        """
        Возвращает нормализованный вектор направления (-1..1, -1..1).
        
        Returns:
            tuple: (x_direction, y_direction) где значения от -1 до 1
        """
        if not self.active:
            return (0, 0)
        
        # Нормализуем к диапазону -1..1
        x_dir = self.handle_x / self.radius
        y_dir = self.handle_y / self.radius
        
        return (x_dir, y_dir)
    
    def get_movement(self, deadzone=0.2):
        """
        Возвращает направление движения с учетом мертвой зоны.
        
        Args:
            deadzone: Минимальное значение для регистрации движения (0..1)
        
        Returns:
            tuple: (x_movement, y_movement) где значения -1, 0, или 1
        """
        x_dir, y_dir = self.get_direction()
        
        # Применяем мертвую зону
        x_movement = 0
        if abs(x_dir) > deadzone:
            x_movement = 1 if x_dir > 0 else -1
        
        y_movement = 0
        if abs(y_dir) > deadzone:
            y_movement = 1 if y_dir > 0 else -1
        
        return (x_movement, y_movement)
    
    def draw(self, screen):
        """Отрисовывает джойстик на экране"""
        # Рисуем внешний круг
        outer_rect = self.outer_surface.get_rect(center=(self.center_x, self.center_y))
        screen.blit(self.outer_surface, outer_rect)
        
        # Рисуем внутренний круг (ручку)
        handle_x = self.center_x + self.handle_x
        handle_y = self.center_y + self.handle_y
        inner_rect = self.inner_surface.get_rect(center=(handle_x, handle_y))
        screen.blit(self.inner_surface, inner_rect)


class MobileControls:
    """Система управления для мобильных устройств с двумя джойстиками"""
    
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        """
        Инициализирует систему управления для мобильных устройств.
        
        Args:
            screen_width, screen_height: Размеры экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Создаем джойстики для двух игроков
        margin = 100
        joystick_radius = 80
        
        # Джойстик для игрока 1 (Аделина) - левая сторона
        self.joystick1 = VirtualJoystick(
            x=margin + joystick_radius,
            y=screen_height - margin - joystick_radius,
            radius=joystick_radius,
            color=(*BLUE[:3], 150)  # Синий для Аделины
        )
        
        # Джойстик для игрока 2 (Аня) - правая сторона
        self.joystick2 = VirtualJoystick(
            x=screen_width - margin - joystick_radius,
            y=screen_height - margin - joystick_radius,
            radius=joystick_radius,
            color=(*RED[:3], 150)  # Красный для Ани
        )
        
        # Кнопка прыжка
        self.jump_button_radius = 60
        self.jump_button_pos = (screen_width - margin - self.jump_button_radius,
                               screen_height - margin - joystick_radius * 2 - 50)
        self.jump_button_pressed = False
        
        # Кнопка действия (поднять/бросить блок)
        self.action_button_radius = 60
        self.action_button_pos = (margin + self.action_button_radius,
                                 screen_height - margin - joystick_radius * 2 - 50)
        self.action_button_pressed = False
    
    def handle_events(self, events):
        """
        Обрабатывает все события для системы управления.
        
        Args:
            events: Список событий pygame
        
        Returns:
            dict: Состояние управления для каждого игрока
        """
        # Сбрасываем состояние кнопок
        self.jump_button_pressed = False
        self.action_button_pressed = False
        
        for event in events:
            # Обрабатываем джойстики
            handled = self.joystick1.handle_event(event)
            if not handled:
                handled = self.joystick2.handle_event(event)
            
            # Обрабатываем кнопки
            if not handled:
                self.handle_button_event(event)
        
        # Возвращаем состояние управления
        return self.get_control_state()
    
    def handle_button_event(self, event):
        """Обрабатывает события для кнопок"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Проверяем кнопку прыжка
            jump_distance = ((mouse_x - self.jump_button_pos[0]) ** 2 + 
                           (mouse_y - self.jump_button_pos[1]) ** 2) ** 0.5
            if jump_distance <= self.jump_button_radius:
                self.jump_button_pressed = True
                return True
            
            # Проверяем кнопку действия
            action_distance = ((mouse_x - self.action_button_pos[0]) ** 2 + 
                             (mouse_y - self.action_button_pos[1]) ** 2) ** 0.5
            if action_distance <= self.action_button_radius:
                self.action_button_pressed = True
                return True
        
        # Обработка сенсорных событий
        elif event.type == pygame.FINGERDOWN:
            touch_x = event.x * self.screen_width
            touch_y = event.y * self.screen_height
            
            jump_distance = ((touch_x - self.jump_button_pos[0]) ** 2 + 
                           (touch_y - self.jump_button_pos[1]) ** 2) ** 0.5
            if jump_distance <= self.jump_button_radius:
                self.jump_button_pressed = True
                return True
            
            action_distance = ((touch_x - self.action_button_pos[0]) ** 2 + 
                             (touch_y - self.action_button_pos[1]) ** 2) ** 0.5
            if action_distance <= self.action_button_radius:
                self.action_button_pressed = True
                return True
        
        return False
    
    def get_control_state(self):
        """
        Возвращает состояние управления для передачи в игру.
        
        Returns:
            dict: Словарь с состояниями клавиш для эмуляции клавиатуры
        """
        # Получаем направление движения от джойстиков
        move1_x, move1_y = self.joystick1.get_movement(deadzone=0.3)
        move2_x, move2_y = self.joystick2.get_movement(deadzone=0.3)
        
        # Создаем словарь состояний клавиш
        # Эмулируем клавиши клавиатуры для совместимости с существующей системой
        keys_state = {
            # Игрок 1 (Аделина) - обычно управляется стрелками
            pygame.K_LEFT: move1_x == -1,
            pygame.K_RIGHT: move1_x == 1,
            pygame.K_UP: self.jump_button_pressed,  # Прыжок по кнопке
            
            # Игрок 2 (Аня) - обычно управляется WASD
            pygame.K_a: move2_x == -1,
            pygame.K_d: move2_x == 1,
            pygame.K_w: self.jump_button_pressed,  # Прыжок по кнопке
            
            # Общие действия
            pygame.K_s: self.action_button_pressed,  # Действие (поднять/бросить)
            pygame.K_DOWN: self.action_button_pressed,  # Альтернативная клавиша
            
            # Остальные клавиши не нажаты
            pygame.K_SPACE: False,
            pygame.K_ESCAPE: False,
            pygame.K_RETURN: False
        }
        
        return keys_state
    
    def draw(self, screen):
        """Отрисовывает все элементы управления на экране"""
        # Рисуем джойстики
        self.joystick1.draw(screen)
        self.joystick2.draw(screen)
        
        # Рисуем кнопку прыжка
        jump_color = (100, 255, 100, 200) if self.jump_button_pressed else (100, 255, 100, 150)
        jump_surface = pygame.Surface((self.jump_button_radius * 2, self.jump_button_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(jump_surface, jump_color, 
                          (self.jump_button_radius, self.jump_button_radius), 
                          self.jump_button_radius)
        jump_rect = jump_surface.get_rect(center=self.jump_button_pos)
        screen.blit(jump_surface, jump_rect)
        
        # Текст на кнопке прыжка
        font = pygame.font.Font(None, 36)
        jump_text = font.render("ПРЫЖОК", True, WHITE)
        jump_text_rect = jump_text.get_rect(center=self.jump_button_pos)
        screen.blit(jump_text, jump_text_rect)
        
        # Рисуем кнопку действия
        action_color = (255, 200, 100, 200) if self.action_button_pressed else (255, 200, 100, 150)
        action_surface = pygame.Surface((self.action_button_radius * 2, self.action_button_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(action_surface, action_color, 
                          (self.action_button_radius, self.action_button_radius), 
                          self.action_button_radius)
        action_rect = action_surface.get_rect(center=self.action_button_pos)
        screen.blit(action_surface, action_rect)
        
        # Текст на кнопке действия
        action_text = font.render("ДЕЙСТВИЕ", True, WHITE)
        action_text_rect = action_text.get_rect(center=self.action_button_pos)
        screen.blit(action_text, action_text_rect)
        
        # Подписи джойстиков
        joystick1_text = font.render("АДЕЛИНА", True, BLUE)
        joystick1_text_rect = joystick1_text.get_rect(center=(self.joystick1.center_x, 
                                                             self.joystick1.center_y - 100))
        screen.blit(joystick1_text, joystick1_text_rect)
        
        joystick2_text = font.render("АНЯ", True, RED)
        joystick2_text_rect = joystick2_text.get_rect(center=(self.joystick2.center_x, 
                                                             self.joystick2.center_y - 100))
        screen.blit(joystick2_text, joystick2_text_rect)


def create_mobile_controls():
    """Создает и возвращает систему управления для мобильных устройств"""
    return MobileControls()