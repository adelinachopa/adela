"""
Загрузчик уровней из JSON файлов для игры "Escape to EMK".
"""
import json
import os
import pygame
from error_handler import GameErrorHandler
import setting  # используем setting.CONSTANT для доступа к константам

class LevelLoader:
    """Загружает и валидирует уровни из JSON файлов"""
    
    @staticmethod
    def load_level(filepath):
        """
        Загружает уровень из JSON файла.
        
        Args:
            filepath (str): Путь к JSON файлу уровня
        
        Returns:
            dict: Данные уровня или уровень по умолчанию при ошибке
        """
        if not os.path.exists(filepath):
            GameErrorHandler.log_error(f"Level file not found: {filepath}", "LevelLoader", "ERROR")
            return LevelLoader.get_default_level()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Базовая валидация
            if not LevelLoader.validate_level_data(data):
                GameErrorHandler.log_error(f"Invalid level data in {filepath}", "LevelLoader", "ERROR")
                return LevelLoader.get_default_level()
            
            # Преобразуем старый формат платформ если нужно
            data = LevelLoader.normalize_level_data(data)
            
            return data
            
        except json.JSONDecodeError as e:
            GameErrorHandler.log_error(f"Invalid JSON in {filepath}: {e}", "LevelLoader", "ERROR")
            return LevelLoader.get_default_level()
        except Exception as e:
            GameErrorHandler.log_error(f"Error loading level {filepath}: {e}", "LevelLoader", "ERROR")
            return LevelLoader.get_default_level()
    
    @staticmethod
    def validate_level_data(data):
        """
        Проверяет структуру данных уровня.
        
        Args:
            data (dict): Данные уровня
        
        Returns:
            bool: True если данные валидны
        """
        # Проверяем обязательные ключи
        required_keys = ['platforms', 'players']
        for key in required_keys:
            if key not in data:
                GameErrorHandler.log_error(f"Missing required key: {key}", "LevelLoader.validate", "ERROR")
                return False
        
        # Проверяем типы
        if not isinstance(data['platforms'], list):
            GameErrorHandler.log_error("Platforms must be a list", "LevelLoader.validate", "ERROR")
            return False
        
        if not isinstance(data['players'], list):
            GameErrorHandler.log_error("Players must be a list", "LevelLoader.validate", "ERROR")
            return False
        
        # Проверяем блоки, если есть (опционально)
        if 'blocks' in data and not isinstance(data['blocks'], list):
            GameErrorHandler.log_error("Blocks must be a list", "LevelLoader.validate", "ERROR")
            return False
        
        # Минимальная проверка платформ
        for i, platform in enumerate(data['platforms']):
            if isinstance(platform, dict):
                required_platform_keys = ['x', 'y', 'width', 'height']
                for key in required_platform_keys:
                    if key not in platform:
                        GameErrorHandler.log_error(f"Platform {i} missing key: {key}", "LevelLoader.validate", "ERROR")
                        return False
            elif isinstance(platform, (list, tuple)):
                if len(platform) < 5:
                    GameErrorHandler.log_error(f"Platform {i} tuple too short: {platform}", "LevelLoader.validate", "ERROR")
                    return False
            else:
                GameErrorHandler.log_error(f"Platform {i} has invalid type: {type(platform)}", "LevelLoader.validate", "ERROR")
                return False
        
        # Проверка игроков
        for i, player in enumerate(data['players']):
            if not isinstance(player, dict):
                GameErrorHandler.log_error(f"Player {i} must be a dict", "LevelLoader.validate", "ERROR")
                return False
            
            required_player_keys = ['x', 'y', 'speed', 'jump_power', 'controls']
            for key in required_player_keys:
                if key not in player:
                    GameErrorHandler.log_error(f"Player {i} missing key: {key}", "LevelLoader.validate", "ERROR")
                    return False
        
        return True
    
    @staticmethod
    def normalize_level_data(data):
        """
        Нормализует данные уровня, преобразуя старые форматы в новые.
        
        Args:
            data (dict): Исходные данные уровня
        
        Returns:
            dict: Нормализованные данные
        """
        normalized = data.copy()
        
        # Нормализация платформ
        platforms = []
        for platform in normalized.get('platforms', []):
            if isinstance(platform, (list, tuple)):
                # Старый формат: (x, y, width, height, texture)
                if len(platform) >= 5:
                    platforms.append({
                        'x': platform[0],
                        'y': platform[1],
                        'width': platform[2],
                        'height': platform[3],
                        'texture': platform[4]
                    })
                else:
                    GameErrorHandler.log_error(f"Invalid platform tuple: {platform}", "LevelLoader.normalize", "WARNING")
            else:
                platforms.append(platform)
        
        normalized['platforms'] = platforms
        
        # Нормализация игроков
        players = []
        for player in normalized.get('players', []):
            normalized_player = player.copy()
            
            # Конвертируем старые ключи
            if 'jump' in normalized_player and 'jump_power' not in normalized_player:
                normalized_player['jump_power'] = normalized_player.pop('jump')
            
            if 'image_path' in normalized_player and 'image' not in normalized_player:
                normalized_player['image'] = normalized_player.pop('image_path')
            
            # Конвертируем цвет из tuple в list если нужно
            if 'color' in normalized_player and isinstance(normalized_player['color'], tuple):
                normalized_player['color'] = list(normalized_player['color'])
            
            players.append(normalized_player)
        
        normalized['players'] = players
        
        # Нормализация врагов
        enemies = []
        for enemy in normalized.get('enemies', []):
            normalized_enemy = enemy.copy()
            
            if 'patrol' in normalized_enemy and 'patrol_range' not in normalized_enemy:
                # Преобразуем старый формат patrol
                patrol = normalized_enemy.pop('patrol')
                if isinstance(patrol, list) and len(patrol) > 0:
                    if isinstance(patrol[0], (list, tuple)):
                        # Формат [(x1, y1), (x2, y2)] -> [x1, x2]
                        x_coords = [p[0] for p in patrol if isinstance(p, (list, tuple)) and len(p) > 0]
                        if len(x_coords) >= 2:
                            normalized_enemy['patrol_range'] = [min(x_coords), max(x_coords)]
            
            if 'image_path' in normalized_enemy and 'image' not in normalized_enemy:
                normalized_enemy['image'] = normalized_enemy.pop('image_path')
            
            enemies.append(normalized_enemy)
        
        normalized['enemies'] = enemies
        # Нормализация блоков
        blocks = []
        for block in normalized.get('blocks', []):
            normalized_block = block.copy()
            
            # Конвертируем старые ключи
            if 'image_path' in normalized_block and 'image' not in normalized_block:
                normalized_block['image'] = normalized_block.pop('image_path')
            
            if 'color' in normalized_block and isinstance(normalized_block['color'], tuple):
                normalized_block['color'] = list(normalized_block['color'])
            
            blocks.append(normalized_block)
        
        normalized['blocks'] = blocks
        
        return normalized
    
    @staticmethod
    def get_default_level():
        """
        Возвращает простой уровень по умолчанию.
        
        Returns:
            dict: Уровень по умолчанию
        """
        return {
            "metadata": {
                "id": "default",
                "name": "Default Level",
                "description": "Fallback level when loading fails",
                "difficulty": 1
            },
            "platforms": [
                {
                    "x": 0,
                    "y": setting.SCREEN_HEIGHT - 40,
                    "width": setting.SCREEN_WIDTH,
                    "height": 40,
                    "texture": setting.PLATFORM_TEX
                }
            ],
            "players": [
                {
                    "x": 100,
                    "y": setting.SCREEN_HEIGHT - 100,
                    "color": list(setting.BLUE),
                    "speed": 5,
                    "jump_power": -10,
                    "controls": {
                        "left": "K_LEFT",
                        "right": "K_RIGHT",
                        "jump": "K_UP"
                    },
                    "image": setting.PLAYER1_IMG
                }
            ],
            "enemies": [
                {
                    "x": 600,
                    "y": 600
                }
            ]
        }
    
    @staticmethod
    def convert_pygame_key(key_string):
        """
        Конвертирует строковое представление клавиши PyGame в код клавиши.
        
        Args:
            key_string (str): Строка с именем клавиши (например, "K_LEFT")
        
        Returns:
            int: Код клавиши PyGame или значение по умолчанию
        """
        if hasattr(pygame, key_string):
            return getattr(pygame, key_string)
        
        # Значения по умолчанию для распространенных клавиш
        default_keys = {
            'K_LEFT': pygame.K_LEFT,
            'K_RIGHT': pygame.K_RIGHT,
            'K_UP': pygame.K_UP,
            'K_DOWN': pygame.K_DOWN,
            'K_a': pygame.K_a,
            'K_d': pygame.K_d,
            'K_w': pygame.K_w,
            'K_s': pygame.K_s,
            'K_SPACE': pygame.K_SPACE,
            'K_ESCAPE': pygame.K_ESCAPE,
            'K_RETURN': pygame.K_RETURN
        }
        
        return default_keys.get(key_string, pygame.K_UP)
    
    @staticmethod
    def convert_controls(controls_dict):
        """
        Конвертирует словарь с строковыми ключами в словарь с кодами клавиш PyGame.
        
        Args:
            controls_dict (dict): Словарь с строковыми именами клавиш
        
        Returns:
            dict: Словарь с кодами клавиш PyGame
        """
        pygame_controls = {}
        for action, key_string in controls_dict.items():
            pygame_controls[action] = LevelLoader.convert_pygame_key(key_string)
        return pygame_controls