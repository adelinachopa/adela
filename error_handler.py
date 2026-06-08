"""
Централизованная система обработки ошибок и логирования для игры "Escape to EMK".
"""
import pygame
from datetime import datetime
import traceback
import sys

class GameErrorHandler:
    """Обработчик ошибок игры"""
    
    LOG_FILE = "game_errors.log"
    
    @staticmethod
    def log_error(error, context="", level="ERROR"):
        """
        Записывает ошибку в лог файл.
        
        Args:
            error: Объект исключения или строка с ошибкой
            context (str): Контекст где произошла ошибка
            level (str): Уровень ошибки (ERROR, WARNING, INFO)
        """
        try:
            error_msg = str(error)
            if isinstance(error, Exception):
                error_msg = f"{type(error).__name__}: {error}"
                # Добавляем traceback для исключений
                tb = traceback.format_exc()
                if tb and tb != "NoneType: None\n":
                    error_msg += f"\nTraceback:\n{tb}"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {context}: {error_msg}\n"
            
            with open(GameErrorHandler.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
                
            # Также выводим в консоль для отладки
            if level == "ERROR":
                print(f"ERROR: {context}: {error_msg}")
            elif level == "WARNING":
                print(f"WARNING: {context}: {error_msg}")
                
        except Exception as e:
            # Если даже логирование не работает, выводим в консоль
            print(f"CRITICAL: Failed to log error: {e}")
    
    @staticmethod
    def load_image_safe(path, width, height, default_color=(255, 255, 255)):
        """
        Безопасная загрузка изображения с обработкой ошибок.
        Использует find_image_file() из setting.py для регистронезависимого поиска.
        
        Args:
            path (str): Путь к файлу изображения
            width (int): Ширина
            height (int): Высота
            default_color (tuple): Цвет по умолчанию
        
        Returns:
            pygame.Surface: Загруженное изображение или поверхность по умолчанию
        """
        if not path:
            surface = pygame.Surface((width, height))
            surface.fill(default_color)
            return surface
        
        try:
            # Используем find_image_file для регистронезависимого поиска
            from setting import find_image_file
            actual_path = find_image_file(path)
            img = pygame.image.load(actual_path)
            return pygame.transform.scale(img, (width, height))
        except Exception as e:
            GameErrorHandler.log_error(e, f"Loading image: {path}", "WARNING")
            
            # Создаем поверхность с цветом по умолчанию
            surface = pygame.Surface((width, height))
            surface.fill(default_color)
            
            # Добавляем текст с именем файла для отладки
            try:
                font = pygame.font.Font(None, 20)
                text = font.render(f"Missing: {path.split('/')[-1]}", True, (255, 0, 0))
                text_rect = text.get_rect(center=(width//2, height//2))
                surface.blit(text, text_rect)
            except:
                pass  # Если не удалось добавить текст, оставляем как есть
            
            return surface
    
    @staticmethod
    def safe_execute(func, default_return=None, context=""):
        """
        Декоратор для безопасного выполнения функции.
        
        Args:
            func: Функция для выполнения
            default_return: Значение по умолчанию при ошибке
            context (str): Контекст для логирования
        
        Returns:
            Результат функции или default_return при ошибке
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                GameErrorHandler.log_error(e, f"{context} in {func.__name__}", "ERROR")
                return default_return
        return wrapper

    @staticmethod
    def check_pygame_initialization():
        """
        Проверяет инициализацию PyGame и его модулей.
        
        Returns:
            bool: True если инициализация успешна, False если есть проблемы
        """
        issues = []
        
        if not pygame.get_init():
            issues.append("PyGame main module not initialized")
        
        if not pygame.display.get_init():
            issues.append("Display module not initialized")
        
        if not pygame.font.get_init():
            issues.append("Font module not initialized")
            # Попробуем инициализировать
            try:
                pygame.font.init()
                if pygame.font.get_init():
                    issues.append("Font module initialized manually")
            except:
                issues.append("Failed to initialize font module")
        
        if issues:
            for issue in issues:
                GameErrorHandler.log_error(issue, "PyGame Initialization", "WARNING")
            return False
        
        return True

# Декоратор для удобного использования
def safe_execute(default_return=None, context=""):
    """
    Декоратор для безопасного выполнения функции с обработкой ошибок.
    
    Args:
        default_return: Значение, возвращаемое при возникновении ошибки
        context (str): Контекст для логирования ошибок
    
    Returns:
        Декоратор функции
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                GameErrorHandler.log_error(e, f"{context} in {func.__name__}", "ERROR")
                return default_return
        return wrapper
    return decorator

# Утилитарные функции для быстрого использования
def log_info(message, context=""):
    """Записывает информационное сообщение в лог."""
    GameErrorHandler.log_error(message, context, "INFO")

def log_warning(message, context=""):
    """Записывает предупреждение в лог."""
    GameErrorHandler.log_error(message, context, "WARNING")

def log_error(message, context=""):
    """Записывает ошибку в лог."""
    GameErrorHandler.log_error(message, context, "ERROR")

# Инициализация при импорте
try:
    # Создаем заголовок в лог файле при первом запуске
    with open(GameErrorHandler.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Game session started: {datetime.now()}\n")
        f.write(f"{'='*60}\n\n")
except:
    pass  # Если не удалось создать лог, продолжаем без него