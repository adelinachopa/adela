# загрузка и управление логики уровнем
import pygame
import os
import setting
from game_platform import Platform
from entities import Player, Enemy, Block, Button, Door, MovingBlock, VerticalButton, Collectible, DoorExit
from level_loader import LevelLoader
from error_handler import GameErrorHandler
from setting import BLUE, RED, WHITE, GREEN, IS_MOBILE, PLAYER_WIDTH, PLAYER_HEIGHT

class Level:
    def __init__(self, level_data_or_path):
        """
        Инициализирует уровень.
        
        Args:
            level_data_or_path: dict с данными уровня или str путь к JSON файлу
        """
        self.platforms = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.buttons = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.moving_blocks = pygame.sprite.Group()  # блоки, двигающиеся по вертикали
        self.vertical_buttons = pygame.sprite.Group()  # кнопки для управления вертикальными блоками
        self.collectibles = pygame.sprite.Group()  # собираемые элементы
        self.door_exits = pygame.sprite.Group()    # двери выхода (активируются двумя персонажами)
        self.solid_objects = pygame.sprite.Group()  # объекты, с которыми сталкиваются игроки и враги
        self.total_collectibles = 0  # общее количество собираемых предметов на уровне
        self.level_data = None
        
        # Определяем тип входных данных
        if isinstance(level_data_or_path, str):
            # Загружаем из файла
            self.level_data = LevelLoader.load_level(level_data_or_path)
            self.level_source = f"file: {os.path.basename(level_data_or_path)}"
        elif isinstance(level_data_or_path, dict):
            # Используем готовые данные
            self.level_data = level_data_or_path
            self.level_source = "dict data"
        else:
            # Неизвестный тип - используем уровень по умолчанию
            error_msg = f"Unknown level data type: {type(level_data_or_path)}"
            GameErrorHandler.log_error(error_msg, "Level.__init__", "ERROR")
            print(f"Warning: {error_msg}")
            self.level_data = LevelLoader.get_default_level()
            self.level_source = "default"
        
        self.load_level(self.level_data)

    def load_level(self, data):
        """Загружает данные уровня с масштабированием под мобильные экраны."""
        # Определяем коэффициент масштабирования (из модуля setting, может быть переопределён в main.py)
        scale = setting.SCALE_FACTOR if IS_MOBILE else 1.0
        
        # Вспомогательная функция для масштабирования координат
        def scale_pos(obj, keys=('x', 'y')):
            for key in keys:
                if key in obj:
                    obj[key] = int(obj[key] * scale)
        
        def scale_size(obj, keys=('width', 'height')):
            for key in keys:
                if key in obj:
                    obj[key] = max(1, int(obj[key] * scale))
        
        # Загрузка платформ
        for plat in data.get('platforms', []):
            if isinstance(plat, dict):
                # Масштабируем координаты и размеры
                if IS_MOBILE:
                    plat_copy = dict(plat)
                    scale_pos(plat_copy)
                    scale_size(plat_copy)
                else:
                    plat_copy = plat
                # Новый формат JSON
                self.platforms.add(Platform(
                    plat_copy['x'], plat_copy['y'],
                    plat_copy['width'], plat_copy['height'],
                    color=plat_copy.get('color'),
                    image_path=plat_copy.get('texture')  # Используем 'texture' вместо 'image_path'
                ))
            else:
                # Старый формат: (x, y, w, h, texture)
                if IS_MOBILE:
                    x = int(plat[0] * scale)
                    y = int(plat[1] * scale)
                    w = max(1, int(plat[2] * scale))
                    h = max(1, int(plat[3] * scale))
                else:
                    x, y, w, h = plat[0], plat[1], plat[2], plat[3]
                self.platforms.add(Platform(x, y, w, h, image_path=plat[4]))
        
        # Загрузка игроков
        for p in data.get('players', []):
            # Конвертируем строковые ключи в pygame коды
            controls_dict = p.get('controls', {})
            pygame_controls = LevelLoader.convert_controls(controls_dict)
            
            # Получаем цвет (может быть list или tuple)
            color = p.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = BLUE  # Значение по умолчанию
            
            # Получаем путь к изображению (может быть 'image' или 'image_path')
            image_path = p.get('image') or p.get('image_path')
            
            # Получаем jump_power (может быть 'jump_power' или 'jump')
            jump_power = p.get('jump_power', p.get('jump', -10))
            
            # Получаем ширину и высоту (опционально)
            width = p.get('width')
            height = p.get('height')
            
            # Масштабируем позицию игрока
            if IS_MOBILE:
                px = int(p['x'] * scale)
                py = int(p['y'] * scale)
                if width is not None:
                    width = max(1, int(width * scale))
                else:
                    width = max(1, int(PLAYER_WIDTH * scale))
                if height is not None:
                    height = max(1, int(height * scale))
                else:
                    height = max(1, int(PLAYER_HEIGHT * scale))
            else:
                px = p['x']
                py = p['y']
            
            self.players.add(Player(
                px, py,
                color,
                p['speed'], jump_power,
                pygame_controls,
                image_path,
                width,
                height
            ))
        
        # Загрузка врагов
        for e in data.get('enemies', []):
            # Получаем цвет
            color = e.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = WHITE  # Значение по умолчанию
            
            # Получаем путь к изображению
            image_path = e.get('image') or e.get('image_path')
            
            # Получаем jump_power
            jump_power = e.get('jump_power', e.get('jump', 3))
            
            # Получаем patrol_range (новый формат) или patrol (старый формат)
            patrol_range = e.get('patrol_range', [300, 500])
            
            # Масштабируем
            if IS_MOBILE:
                ex = int(e['x'] * scale)
                ey = int(e['y'] * scale)
                esize = max(1, int(e.get('size', 80) * scale))
                patrol_range = [int(x * scale) for x in patrol_range]
            else:
                ex = e['x']
                ey = e['y']
                esize = e.get('size', 80)
            
            self.enemies.add(Enemy(
                ex, ey,
                esize,
                color,
                e['speed'], jump_power,
                patrol_range,
                image_path
            ))
        
        # Загрузка блоков
        for b in data.get('blocks', []):
            # Получаем цвет
            color = b.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (200, 100, 50)  # цвет по умолчанию
            
            # Получаем путь к изображению
            image_path = b.get('image') or b.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                bx = int(b['x'] * scale)
                by = int(b['y'] * scale)
                width = max(1, int(b.get('width', 40) * scale))
                height = max(1, int(b.get('height', 40) * scale))
            else:
                bx = b['x']
                by = b['y']
                width = b.get('width', 40)
                height = b.get('height', 40)
            
            # Получаем флаг pushable_only (блок можно только толкать, нельзя поднимать)
            pushable_only = b.get('pushable_only', False)
            
            self.blocks.add(Block(
                bx, by,
                width, height,
                color,
                image_path,
                pushable_only
            ))
        
        # Загрузка кнопок
        for btn in data.get('buttons', []):
            # Получаем цвет (опционально)
            color = btn.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (100, 200, 100)  # зелёный по умолчанию
            
            # Получаем путь к изображению
            image_path = btn.get('image') or btn.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                btnx = int(btn['x'] * scale)
                btny = int(btn['y'] * scale)
                width = max(1, int(btn.get('width', 40) * scale))
                height = max(1, int(btn.get('height', 20) * scale))
            else:
                btnx = btn['x']
                btny = btn['y']
                width = btn.get('width', 40)
                height = btn.get('height', 20)
            
            # Получаем ID двери
            door_id = btn.get('door_id')
            # Получаем режим рычага (по умолчанию False)
            toggle = btn.get('toggle', False)
            
            self.buttons.add(Button(
                btnx, btny,
                width, height,
                image_path,
                door_id,
                toggle
            ))
        
        # Загрузка дверей
        for dr in data.get('doors', []):
            # Получаем цвет (опционально)
            color = dr.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (255, 255, 0)  # жёлтый по умолчанию
            
            # Получаем путь к изображению
            image_path = dr.get('image') or dr.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                drx = int(dr['x'] * scale)
                dry = int(dr['y'] * scale)
                width = max(1, int(dr.get('width', 80) * scale))
                height = max(1, int(dr.get('height', 20) * scale))
            else:
                drx = dr['x']
                dry = dr['y']
                width = dr.get('width', 80)
                height = dr.get('height', 20)
            
            # Получаем ID двери
            door_id = dr.get('door_id')
            
            # Получаем ориентацию (горизонтальная по умолчанию)
            horizontal = dr.get('horizontal', True)
            
            self.doors.add(Door(
                drx, dry,
                width, height,
                image_path,
                door_id,
                horizontal
            ))
        
        # Загрузка вертикальных блоков (moving_blocks)
        for mb in data.get('moving_blocks', []):
            # Получаем цвет
            color = mb.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (150, 150, 200)  # цвет по умолчанию
            
            # Получаем путь к изображению
            image_path = mb.get('image') or mb.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                mbx = int(mb['x'] * scale)
                mby = int(mb['y'] * scale)
                width = max(1, int(mb.get('width', 40) * scale))
                height = max(1, int(mb.get('height', 40) * scale))
                move_speed = mb.get('move_speed', 3) * scale
                move_range = int(mb.get('move_range', 200) * scale)
            else:
                mbx = mb['x']
                mby = mb['y']
                width = mb.get('width', 40)
                height = mb.get('height', 40)
                move_speed = mb.get('move_speed', 3)
                move_range = mb.get('move_range', 200)
            
            move_up = mb.get('move_up', False)
            block_id = mb.get('block_id')
            
            moving_block = MovingBlock(
                mbx, mby,
                width, height,
                color,
                image_path,
                move_speed,
                move_range,
                move_up
            )
            if block_id:
                moving_block.block_id = block_id
            self.moving_blocks.add(moving_block)
        
        # Загрузка вертикальных кнопок (vertical_buttons)
        for vb in data.get('vertical_buttons', []):
            # Получаем цвет
            color = vb.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (200, 100, 200)  # цвет по умолчанию
            
            # Получаем путь к изображению
            image_path = vb.get('image') or vb.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                vbx = int(vb['x'] * scale)
                vby = int(vb['y'] * scale)
                width = max(1, int(vb.get('width', 40) * scale))
                height = max(1, int(vb.get('height', 20) * scale))
            else:
                vbx = vb['x']
                vby = vb['y']
                width = vb.get('width', 40)
                height = vb.get('height', 20)
            
            # Получаем ID блока
            block_id = vb.get('block_id')
            
            self.vertical_buttons.add(VerticalButton(
                vbx, vby,
                width, height,
                image_path,
                block_id
            ))
        
        # Загрузка собираемых элементов (collectibles)
        for col in data.get('collectibles', []):
            # Получаем цвет
            color = col.get('color')
            if isinstance(color, list):
                color = tuple(color)
            elif color is None:
                color = (255, 255, 0)  # жёлтый по умолчанию
            
            # Получаем путь к изображению
            image_path = col.get('image') or col.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                colx = int(col['x'] * scale)
                coly = int(col['y'] * scale)
                width = max(1, int(col.get('width', 50) * scale))
                height = max(1, int(col.get('height', 50) * scale))
            else:
                colx = col['x']
                coly = col['y']
                width = col.get('width', 50)
                height = col.get('height', 50)
            
            # Получаем ID элемента (опционально)
            item_id = col.get('item_id')
            
            self.collectibles.add(Collectible(
                colx, coly,
                width, height,
                image_path,
                color,
                item_id
            ))
        
        # Загрузка дверей выхода (door_exits)
        for de in data.get('door_exits', []):
            # Получаем путь к изображению
            image_path = de.get('image') or de.get('image_path')
            
            # Получаем размеры (опционально)
            if IS_MOBILE:
                dex = int(de['x'] * scale)
                dey = int(de['y'] * scale)
                width = max(1, int(de.get('width', 100) * scale))
                height = max(1, int(de.get('height', 150) * scale))
            else:
                dex = de['x']
                dey = de['y']
                width = de.get('width', 100)
                height = de.get('height', 150)
            
            # Получаем размеры экрана для UI (опционально)
            screen_width = de.get('screen_width', 1280)
            screen_height = de.get('screen_height', 720)
            
            self.door_exits.add(DoorExit(
                dex, dey,
                width, height,
                image_path,
                screen_width,
                screen_height
            ))
        
        # Логирование успешной загрузки
        platform_count = len(data.get('platforms', []))
        player_count = len(data.get('players', []))
        enemy_count = len(data.get('enemies', []))
        block_count = len(data.get('blocks', []))
        button_count = len(data.get('buttons', []))
        door_count = len(data.get('doors', []))
        moving_block_count = len(data.get('moving_blocks', []))
        vertical_button_count = len(data.get('vertical_buttons', []))
        collectible_count = len(data.get('collectibles', []))
        door_exit_count = len(data.get('door_exits', []))
        
        GameErrorHandler.log_error(
            f"Level loaded: {platform_count} platforms, {player_count} players, {enemy_count} enemies, {block_count} blocks, {button_count} buttons, {door_count} doors, {moving_block_count} moving_blocks, {vertical_button_count} vertical_buttons, {collectible_count} collectibles, {door_exit_count} door_exits",
            "Level.load_level",
            "INFO"
        )
        
        # Сохраняем общее количество собираемых предметов
        self.total_collectibles = collectible_count
        
        # Инициализируем solid_objects: платформы, двери и движущиеся блоки (твёрдые объекты)
        self.solid_objects.empty()
        self.solid_objects.add(*self.platforms)
        self.solid_objects.add(*self.doors)
        self.solid_objects.add(*self.moving_blocks)

    def update(self, level_complete=False, level_failed=False):
        # Если уровень завершён или проигран, останавливаем игроков и врагов
        if not level_complete and not level_failed:
            for player in self.players:
                player.update(self.solid_objects)
            self.resolve_player_collisions()
            
            # Обновляем врагов и собираем мёртвых
            dead_enemies = []
            for enemy in self.enemies:
                enemy.update(self.solid_objects)
                if not enemy.alive:
                    dead_enemies.append(enemy)
            
            # Удаляем мёртвых врагов из группы
            for enemy in dead_enemies:
                self.enemies.remove(enemy)
        else:
            # Останавливаем движение игроков (обнуляем скорости)
            for player in self.players:
                player.vx = 0
                player.vy = 0
            # Враги остаются на месте (не обновляем)
        
        # Блоки, кнопки, двери продолжают работать (для анимаций)
        for block in self.blocks:
            block.update(self.platforms, self.players, self.enemies, self.doors)
        for button in self.buttons:
            button.update(self.players, self.doors, self.blocks)
        for door in self.doors:
            door.update()
        
        # Обновляем вертикальные блоки и кнопки
        for moving_block in self.moving_blocks:
            moving_block.update(self.platforms)
        for vertical_button in self.vertical_buttons:
            vertical_button.update(self.players, self.moving_blocks, self.blocks)
        
        # Обновляем собираемые элементы (коллизия с игроками)
        for collectible in self.collectibles:
            collectible.update(self.players)
        
        # Вычисляем количество собранных предметов
        collected = self.total_collectibles - len(self.collectibles)
        
        # Обновляем двери выхода (проверка активации)
        for door_exit in self.door_exits:
            door_exit.update(self.players, collected, self.total_collectibles)

    def draw(self, screen):
        # Отладочный вывод состояния игроков перед отрисовкой
        for i, player in enumerate(self.players):
            GameErrorHandler.log_error(
                f"Drawing player {i}: rect={player.rect}, image={'exists' if player.image else 'None'}, visible={player.visible if hasattr(player, 'visible') else 'N/A'}",
                "Level.draw",
                "DEBUG"
            )
        self.platforms.draw(screen)
        self.doors.draw(screen)
        self.moving_blocks.draw(screen)
        self.vertical_buttons.draw(screen)
        self.collectibles.draw(screen)
        self.door_exits.draw(screen)
        self.players.draw(screen)
        self.enemies.draw(screen)
        self.blocks.draw(screen)
        self.buttons.draw(screen)
    
    def check_collisions(self):
        """Возвращает True, если хотя бы один игрок столкнулся с живым врагом"""
        for player in self.players:
            # Проверяем столкновение игрока с любым врагом
            collided_enemies = pygame.sprite.spritecollide(player, self.enemies, False)
            for enemy in collided_enemies:
                if enemy.alive:  # только живые враги считаются
                    return True
        return False
    
    def resolve_player_collisions(self):
        players_list = list(self.players)
        for i in range(len(players_list)):
            for j in range(i + 1, len(players_list)):
                p1 = players_list[i]  # Аделя (стрелки)
                p2 = players_list[j]  # Аня (WASD)
                if not p1.rect.colliderect(p2.rect):
                    continue

                dx = p1.rect.centerx - p2.rect.centerx
                dy = p1.rect.centery - p2.rect.centery

                # Горизонтальное перекрытие больше вертикального
                if abs(dx) > abs(dy):
                    # Аделя справа от Ани
                    if dx > 0:
                        if p1.vx < 0:  # Аделя двигается влево (навстречу)
                            # Сохраняем старую позицию
                            old_right = p2.rect.right
                            p2.rect.right = p1.rect.left
                            # Проверяем, не столкнётся ли Аня с твёрдыми объектами после сдвига
                            if pygame.sprite.spritecollideany(p2, self.solid_objects):
                                p2.rect.right = old_right  # откатываем, если есть коллизия
                        else:
                            if p2.rect.right > p1.rect.left:
                                old_right = p2.rect.right
                                p2.rect.right = p1.rect.left
                                if pygame.sprite.spritecollideany(p2, self.solid_objects):
                                    p2.rect.right = old_right
                    else:  # Аделя слева от Ани
                        if p1.vx > 0:  # Аделя двигается вправо (навстречу)
                            old_left = p2.rect.left
                            p2.rect.left = p1.rect.right
                            if pygame.sprite.spritecollideany(p2, self.solid_objects):
                                p2.rect.left = old_left
                        else:
                            if p2.rect.left < p1.rect.right:
                                old_left = p2.rect.left
                                p2.rect.left = p1.rect.right
                                if pygame.sprite.spritecollideany(p2, self.solid_objects):
                                    p2.rect.left = old_left
                    # Обнуляем горизонтальную скорость Ани, если она упирается
                    if (p2.vx > 0 and p2.rect.left <= p1.rect.right) or (p2.vx < 0 and p2.rect.right >= p1.rect.left):
                        p2.vx = 0
                else:
                    # Вертикальное перекрытие (или равное)
                    if dy > 0:  # p1 ниже p2 -> p2 сверху
                        # Проверяем, не стоит ли p2 на блоке (тогда p1 не должен поднимать p2)
                        p2_on_block = False
                        for block in self.blocks:
                            if block.rect.top <= p2.rect.bottom <= block.rect.top + 5 and abs(p2.rect.centerx - block.rect.centerx) < block.rect.width:
                                p2_on_block = True
                                break
                        if not p2_on_block and p2.vy > 0:
                            old_bottom = p2.rect.bottom
                            p2.rect.bottom = p1.rect.top
                            if pygame.sprite.spritecollideany(p2, self.solid_objects):
                                p2.rect.bottom = old_bottom
                            else:
                                p2.vy = 0
                                p2.on_ground = True
                    else:       # p1 выше p2
                        # Проверяем, не стоит ли p1 на блоке (тогда p2 не должен поднимать p1)
                        p1_on_block = False
                        for block in self.blocks:
                            if block.rect.top <= p1.rect.bottom <= block.rect.top + 5 and abs(p1.rect.centerx - block.rect.centerx) < block.rect.width:
                                p1_on_block = True
                                break
                        if not p1_on_block and p1.vy > 0:
                            old_bottom = p1.rect.bottom
                            p1.rect.bottom = p2.rect.top
                            if pygame.sprite.spritecollideany(p1, self.solid_objects):
                                p1.rect.bottom = old_bottom
                            else:
                                p1.vy = 0
                                p1.on_ground = True
    
    
    
    
    
    
    
    
    
    