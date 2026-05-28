# классы пользователй и ботов
import pygame
import time
from setting import *
from error_handler import GameErrorHandler

class Entity(pygame.sprite.Sprite):
    """Базовый класс для всех подвижных объектов"""
    def __init__(self, x, y, width, height, color=None, image_path=None):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if image_path:
            self.image = load_image(image_path, width, height)
        else:
            self.image = pygame.Surface((width, height))
            if color:
                self.image.fill(color)
            else:
                self.image.fill(WHITE)  # дефолт
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Уменьшаем rect для коллизий (убираем прозрачные края)
        # Коэффициенты масштабирования: ширина 80%, высота 90%
        scale_w = 0.8
        scale_h = 1
        new_width = int(self.rect.width * scale_w)
        new_height = int(self.rect.height * scale_h)
        # Изменяем размер rect относительно центра
        self.rect.inflate_ip(new_width - self.rect.width, new_height - self.rect.height)
        
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.color = color  # сохраняем цвет для идентификации

    def apply_gravity(self):
        if not self.on_ground:
            self.vy += GRAVITY
            # Ограничение максимальной скорости падения
            if self.vy > MAX_FALL_SPEED:
                self.vy = MAX_FALL_SPEED

    def update(self):
        pass

class Player(Entity):
    def __init__(self, x, y, color, speed, jump, controls, image_path=None, width=None, height=None):
        # Если width/height не указаны, используем значения по умолчанию из setting.py
        if width is None:
            width = PLAYER_WIDTH
        if height is None:
            height = PLAYER_HEIGHT
        super().__init__(x, y, width, height, color, image_path)
        self.controls = controls  # словарь с клавишами: left, right, jump
        self.speed = speed
        self.jump = jump
        self.carried_block = None  # блок, который несёт игрок
        self.pickup_cooldown = 0  # таймер для защиты от мгновенного броска
        # Сохраняем исходное изображение и вычисляем путь к изображению с блоком
        self.original_image = self.image.copy() if self.image else None
        self.block_image = None
        if image_path:
            # Пытаемся определить путь к изображению с блоком
            # Например, если image_path = "image/sprite/adelina.png", то block_path = "image/sprite/Adelina_block.jpg"
            import os
            dir_name = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            # Убираем расширение
            name_without_ext = os.path.splitext(base_name)[0]
            # Пробуем несколько вариантов
            possible_names = [
                f"{name_without_ext}_block.jpg",
                f"{name_without_ext}_block.png",
                f"Adelina_block.jpg",  # специально для Аделины
            ]
            for block_name in possible_names:
                block_path = os.path.join(dir_name, block_name)
                if os.path.exists(block_path):
                    self.block_image = load_image(block_path, width, height)
                    break

    def switch_to_block_image(self):
        """Переключить изображение на вариант с блоком, если он есть."""
        if self.block_image is not None:
            self.image = self.block_image
            # Обновляем rect, чтобы размеры соответствовали (хотя они должны быть одинаковыми)
            current_center = self.rect.center
            self.rect = self.image.get_rect(center=current_center)

    def switch_to_original_image(self):
        """Вернуть исходное изображение."""
        if self.original_image is not None:
            self.image = self.original_image
            current_center = self.rect.center
            self.rect = self.image.get_rect(center=current_center)

    def handle_input(self, keys):
        self.vx = 0
        if keys[self.controls['left']]:
            self.vx = -self.speed
        if keys[self.controls['right']]:
            self.vx = self.speed
        if keys[self.controls['jump']] and self.on_ground:
            self.vy = self.jump
            self.on_ground = False

    def handle_block_interaction(self, keys, blocks):
        """
        Обработка взаимодействия с блоками: поднятие и бросок.
        Вызывается после handle_input.
        Только игроки, у которых в controls есть клавиша 'down', могут поднимать и бросать блоки.
        """
        # Определяем клавишу "вниз" - если нет в controls, игрок не может взаимодействовать с блоками
        down_key = self.controls.get('down')
        if down_key is None:
            return  # у этого игрока нет клавиши для взаимодействия с блоками
        
        if keys[down_key]:
            # Если уже несём блок, бросаем его только если нет кулдауна
            if self.carried_block is not None and self.pickup_cooldown == 0:
                direction = 1 if self.vx >= 0 else -1  # направление в сторону движения или вправо по умолчанию
                self.carried_block.throw(direction)
                self.carried_block = None
                self.switch_to_original_image()
                # Устанавливаем кулдаун после броска, чтобы не поднять блок сразу же
                self.pickup_cooldown = 10
            elif self.carried_block is None:
                # Попытаться поднять ближайший блок
                for block in blocks:
                    if block.carried_by is None and not block.thrown:
                        # Проверяем, находится ли блок достаточно близко (по горизонтали и вертикали)
                        # Горизонтальное расстояние: центр блока должен быть в пределах ширины игрока * 1.5
                        horizontal_close = abs(block.rect.centerx - self.rect.centerx) < self.rect.width * 1.5
                        # Вертикальное расстояние: блок должен быть не выше головы игрока и не ниже его ног
                        vertical_close = (block.rect.bottom >= self.rect.top - 10 and
                                         block.rect.top <= self.rect.bottom + 10)
                        # Также проверяем, что блок находится перед игроком (по направлению движения)
                        # Если игрок движется вправо (vx > 0), блок должен быть справа от центра игрока
                        # Если движется влево (vx < 0), блок должен быть слева
                        # Если стоит на месте, можно поднять блок с любой стороны
                        if self.vx > 0:
                            in_front = block.rect.centerx > self.rect.centerx - self.rect.width // 2
                        elif self.vx < 0:
                            in_front = block.rect.centerx < self.rect.centerx + self.rect.width // 2
                        else:
                            in_front = True  # если стоит, можно поднять с любой стороны
                        
                        if horizontal_close and vertical_close and in_front:
                            if block.pick_up(self):
                                self.carried_block = block
                                self.switch_to_block_image()
                                # Устанавливаем кулдаун после поднятия, чтобы не бросить блок сразу же
                                self.pickup_cooldown = 10
                                break

    def update(self, platforms):
        self.apply_gravity()
        # Движение по X
        self.rect.x += self.vx
        self.collide(self.vx, 0, platforms)
        # Движение по Y
        self.rect.y += self.vy
        self.on_ground = False
        self.collide(0, self.vy, platforms)
        # Уменьшаем таймер защиты от мгновенного броска
        if self.pickup_cooldown > 0:
            self.pickup_cooldown -= 1

    def collide(self, dx, dy, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0:  # вправо
                    self.rect.right = platform.rect.left
                if dx < 0:  # влево
                    self.rect.left = platform.rect.right
                if dy > 0:  # падение вниз
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.on_ground = True
                if dy < 0:  # прыжок вверх (удар головой)
                    self.rect.top = platform.rect.bottom
                    self.vy = 0

class Enemy(Entity):
    def __init__(self, x, y, size, color, speed, jump, patrol_points, image_path=None, width=None, height=None):
        # Если width и height указаны, используем их; иначе используем size для обоих
        actual_width = width if width is not None else size
        actual_height = height if height is not None else size
        super().__init__(x, y, actual_width, actual_height, color, image_path)
        # Устанавливаем флаг жизни
        self.alive = True  # флаг жизни врага
        
        # Поддержка разных форматов patrol_points
        # 1. Старый формат: [(x1, y1), (x2, y2)]
        # 2. Новый формат: [min_x, max_x] (патрулирование по горизонтали)
        self.patrol_points = self._normalize_patrol_points(patrol_points, x, y)
        
        self.patrol_index = 0
        self.speed = speed
        self.jump = jump
    
    def die(self):
        """Убить врага - останавливает движение и патрулирование"""
        self.alive = False
        self.vx = 0
        self.vy = 0
        # Враг остаётся в группе, но не двигается и не участвует в коллизиях
    
    def _normalize_patrol_points(self, patrol_data, start_x, start_y):
        """
        Нормализует данные патрулирования в стандартный формат.
        
        Args:
            patrol_data: Данные патрулирования (разные форматы)
            start_x: Начальная X координата врага
            start_y: Начальная Y координата врага
        
        Returns:
            list: Список кортежей [(x1, y1), (x2, y2), ...]
        """
        if not patrol_data:
            # Значение по умолчанию: патрулирование вокруг начальной позиции
            return [(start_x - 100, start_y), (start_x + 100, start_y)]
        
        if isinstance(patrol_data, list):
            if len(patrol_data) == 2 and all(isinstance(x, (int, float)) for x in patrol_data):
                # Новый формат: [min_x, max_x]
                min_x, max_x = patrol_data
                return [(min_x, start_y), (max_x, start_y)]
            elif all(isinstance(point, (list, tuple)) and len(point) == 2 for point in patrol_data):
                # Старый формат: [(x1, y1), (x2, y2)]
                return [(point[0], point[1]) for point in patrol_data]
        
        # Если формат неизвестен, используем значение по умолчанию
        return [(start_x - 100, start_y), (start_x + 100, start_y)]

    def update(self, platforms):
        # Если враг мёртв, не обновляем его состояние
        if not self.alive:
            return
        
        # Движение к текущей точке патруля
        target_x, target_y = self.patrol_points[self.patrol_index]
        dx = target_x - self.rect.x
        dy = target_y - self.rect.y
        if abs(dx) > self.speed:
            self.vx = self.speed if dx > 0 else -self.speed
        else:
            self.vx = dx
        if abs(dy) > self.speed:
            self.vy = self.speed if dy > 0 else -self.speed
        else:
            self.vy = dy

        self.apply_gravity()
        self.rect.x += self.vx
        self.collide(self.vx, 0, platforms)
        self.rect.y += self.vy
        self.on_ground = False
        self.collide(0, self.vy, platforms)

        # Если достигли цели, переключаемся на следующую точку
        if abs(dx) < self.speed and abs(dy) < self.speed:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)

    def collide(self, dx, dy, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                if dx < 0:
                    self.rect.left = platform.rect.right
                if dy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.on_ground = True
                if dy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vy = 0
                    self.on_ground = False
























































# Аделина
# adeline_rect = pygame.Rect(100, 400, 40, 40)
# adeline_speed = 4
# adeline_color = BLUE

# Аня
# anya_rect = pygame.Rect(150, 400, 25, 25)
# anya_speed = 6
# anya_color = RED

# def walk(keys):   # Управление стрелками
#     dx_adeline, dy_adeline = 0, 0
#     if keys[pygame.K_LEFT]:
#         dx_adeline = -adeline_speed
#     if keys[pygame.K_RIGHT]:
#         dx_adeline = adeline_speed
#     if keys[pygame.K_UP]:
#         dy_adeline = -adeline_speed
#     if keys[pygame.K_DOWN]:
#         dy_adeline = adeline_speed
        
# # Управление WASD
#     dx_anya, dy_anya = 0, 0
#     if keys[pygame.K_a]:
#         dx_anya = -anya_speed
#     if keys[pygame.K_d]:
#         dx_anya = anya_speed
#     if keys[pygame.K_w]:
#         dy_anya = -anya_speed
#     if keys[pygame.K_s]:
class Block(Entity):
    """Класс блока, который можно поднимать и бросать"""
    def __init__(self, x, y, width=40, height=40, color=(200, 100, 50), image_path=None, pushable_only=False):
        super().__init__(x, y, width, height, color, image_path)
        self.carried_by = None  # ссылка на игрока, который несёт блок
        self.thrown = False     # флаг броска
        self.throw_vx = 0
        self.throw_vy = 0
        self.throw_time = 0     # время с момента броска (для траектории)
        self.has_been_pushed = False  # флаг, что блок был толкнут игроком
        self.is_vertical = height > width  # блок вертикальный (высота больше ширины)
        self.pushable_only = pushable_only  # блок можно только толкать, нельзя поднимать
    
    def update(self, platforms, players=None, enemies=None, doors=None):
        """
        Обновление состояния блока: если брошен, двигаем по траектории.
        Также проверяет коллизии с игроками и врагами, если они переданы.
        """
        if self.carried_by is not None:
            # Блок несётся игроком - позиция над головой
            # Жёстко привязываем блок к позиции игрока
            self.rect.midbottom = self.carried_by.rect.midtop
            self.rect.y -= 5  # небольшой отступ от головы
            self.vx = 0
            self.vy = 0
            # Не проверяем коллизии с платформами, чтобы блок не телепортировался
            # Если игрок столкнётся с платформой, он сам остановится, блок останется над головой
        elif self.thrown:
            # Движение по траектории броска
            self.rect.x += self.throw_vx
            self.rect.y += self.throw_vy
            self.throw_vy += GRAVITY  # гравитация влияет
            self.throw_time += 1
            # Проверка коллизий с платформами
            self._check_collision(platforms)
            # Проверка коллизий с дверьми
            if doors is not None:
                self._check_door_collision(doors)
        else:
            # Обычное падение под гравитацией
            # Флаг on_ground будет сброшен в _check_collision при отсутствии коллизий
            if not self.on_ground:
                self.apply_gravity()
            self.rect.y += self.vy
            self._check_collision(platforms)
            # Проверка коллизий с дверьми
            if doors is not None:
                self._check_door_collision(doors)
        
        # Проверка коллизий с сущностями (игроками и врагами)
        if players is not None and enemies is not None:
            self.check_entity_collisions(players, enemies, platforms)
    
    def _check_collision(self, platforms):
        """Проверка столкновений с платформами"""
        ground_collision = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Определяем, какая вертикальная скорость используется
                vertical_velocity = self.throw_vy if self.thrown else self.vy
                vertical_collision = False
                # Если падаем вниз
                if vertical_velocity > 0:
                    self.rect.bottom = platform.rect.top
                    if self.thrown:
                        self.thrown = False  # прекращаем бросок при приземлении
                        self.throw_vx = 0
                        self.throw_vy = 0
                    else:
                        # Блок теперь стоит на земле
                        self.vy = 0
                    self.on_ground = True
                    vertical_collision = True
                    ground_collision = True
                # Если движемся вверх (редко)
                elif vertical_velocity < 0:
                    self.rect.top = platform.rect.bottom + COLLISION_EPSILON
                    if self.thrown:
                        self.throw_vy = self.throw_vy * BOUNCE_FACTOR
                    else:
                        self.vy = self.vy * BOUNCE_FACTOR
                    # Блок ударился головой, не стоит на земле
                    self.on_ground = False
                    vertical_collision = True
                # Если вертикальная скорость равна 0, но блок стоит на платформе
                elif vertical_velocity == 0:
                    # Проверяем, что блок находится над платформой (нижняя граница блока близка к верхней границе платформы)
                    if self.rect.bottom <= platform.rect.top + COLLISION_EPSILON and self.rect.bottom >= platform.rect.top - COLLISION_EPSILON:
                        # Блок уже стоит на платформе
                        self.on_ground = True
                        ground_collision = True
                        vertical_collision = True
                
                # Горизонтальные коллизии (если есть горизонтальная скорость и не было вертикальной коллизии)
                if not vertical_collision:
                    if self.thrown and self.throw_vx > 0:
                        self.rect.right = platform.rect.left - COLLISION_EPSILON
                        self.throw_vx = self.throw_vx * BOUNCE_FACTOR
                    elif self.thrown and self.throw_vx < 0:
                        self.rect.left = platform.rect.right + COLLISION_EPSILON
                        self.throw_vx = self.throw_vx * BOUNCE_FACTOR
                    elif not self.thrown and self.carried_by is None:
                        # Блок толкают (не брошен) — проверяем горизонтальные коллизии
                        # Определяем направление движения по разнице позиций
                        # Сравниваем центр блока и центр платформы
                        dx = self.rect.centerx - platform.rect.centerx
                        if dx > 0:
                            # Блок справа от платформы — толкаем вправо, упёрлись левой стороной
                            self.rect.left = platform.rect.right + COLLISION_EPSILON
                        else:
                            # Блок слева от платформы — толкаем влево, упёрлись правой стороной
                            self.rect.right = platform.rect.left - COLLISION_EPSILON
                
                # После обработки коллизии с одной платформой выходим из цикла
                break
        # Если не было коллизии снизу, блок не на земле
        if not ground_collision:
            self.on_ground = False
    
    def _check_door_collision(self, doors):
        """
        Проверка столкновений блока с дверьми.
        Блок не может проходить сквозь закрытые двери.
        Если дверь открывается, блок проваливается сквозь неё.
        """
        for door in doors:
            if self.rect.colliderect(door.rect):
                if door.opened:
                    # Дверь открыта — блок проходит сквозь неё
                    # on_ground будет сброшен в _check_collision, если нет платформы под блоком
                    continue
                
                # Дверь закрыта — блок не может пройти сквозь неё
                # Определяем направление коллизии
                dx = self.rect.centerx - door.rect.centerx
                dy = self.rect.centery - door.rect.centery
                
                # Вертикальная скорость блока
                vertical_velocity = self.throw_vy if self.thrown else self.vy
                
                # Если блок падает на дверь сверху
                if vertical_velocity >= 0 and dy < 0:
                    self.rect.bottom = door.rect.top
                    if self.thrown:
                        self.thrown = False
                        self.throw_vx = 0
                        self.throw_vy = 0
                    else:
                        self.vy = 0
                    self.on_ground = True
                # Если блок снизу двери (движется вверх)
                elif vertical_velocity < 0 and dy > 0:
                    self.rect.top = door.rect.bottom
                    if self.thrown:
                        self.throw_vy = self.throw_vy * BOUNCE_FACTOR
                    else:
                        self.vy = 0
                # Горизонтальная коллизия
                elif abs(dx) > abs(dy):
                    if dx > 0:  # блок справа от двери
                        self.rect.left = door.rect.right
                    else:  # блок слева от двери
                        self.rect.right = door.rect.left
                    if self.thrown:
                        self.throw_vx = self.throw_vx * BOUNCE_FACTOR
                # Если блок стоит на двери (вертикальная коллизия сверху)
                else:
                    self.rect.bottom = door.rect.top
                    if self.thrown:
                        self.thrown = False
                        self.throw_vx = 0
                        self.throw_vy = 0
                    else:
                        self.vy = 0
                    self.on_ground = True
                break  # обработали коллизию с первой дверью
    
    def check_entity_collisions(self, players, enemies, platforms):
        """
        Проверка столкновений блока с игроками и врагами.
        Обрабатывает коллизии, чтобы блок был твёрдым объектом.
        Также реализует толкание блока, если сущность движется.
        """
        # Объединяем всех сущностей
        entities = list(players) + list(enemies)
        for entity in entities:
            # Пропускаем самого себя (если блок является сущностью? нет)
            # Пропускаем игрока, который несёт этот блок
            if hasattr(entity, 'carried_block') and entity.carried_block == self:
                continue
            if self.rect.colliderect(entity.rect):
                # Отладочный вывод
                if hasattr(entity, 'controls'):
                    GameErrorHandler.log_error(
                        f"Block collision with player {entity.rect} at ({self.rect.x}, {self.rect.y}), dx={self.rect.centerx - entity.rect.centerx}, dy={self.rect.centery - entity.rect.centery}, vx={entity.vx if hasattr(entity, 'vx') else 'N/A'}",
                        "Block.check_entity_collisions",
                        "DEBUG"
                    )
                
                # Определяем направление коллизии
                dx = self.rect.centerx - entity.rect.centerx
                dy = self.rect.centery - entity.rect.centery
                
                # Определяем вертикальную скорость блока
                vertical_velocity = self.throw_vy if self.thrown else self.vy
                
                # Если блок падает на сущность (движется вниз и находится выше сущности)
                if vertical_velocity > 0 and dy < 0 and self.carried_by is None:
                    # Проверяем, является ли сущность врагом и скорость падения достаточна для убийства
                    if hasattr(entity, 'patrol_points') and vertical_velocity > 5:
                        # Убиваем врага
                        if hasattr(entity, 'die'):
                            entity.die()
                        # Блок продолжает падать (не приземляется на врага)
                        # Не обнуляем скорость и не меняем позицию блока
                        # Пропускаем остальную обработку для этой сущности
                        continue
                    # Обычное приземление на сущность
                    self.rect.bottom = entity.rect.top
                    if self.thrown:
                        self.thrown = False  # прекращаем бросок
                        self.throw_vx = 0
                        self.throw_vy = 0
                    else:
                        self.vy = 0
                    self.on_ground = True  # блок стоит на сущности
                    continue  # дальше не обрабатываем горизонтальную коллизию
                
                # Если горизонтальное перекрытие больше вертикального (с небольшим смещением в пользу горизонтальной коллизии)
                if abs(dx) > abs(dy) - 5:
                    # Определяем направление толкания
                    push_direction = 0
                    if dx < 0 and hasattr(entity, 'vx') and entity.vx < 0:
                        # Сущность движется влево, блок слева - толкаем влево
                        push_direction = -1
                    elif dx > 0 and hasattr(entity, 'vx') and entity.vx > 0:
                        # Сущность движется вправо, блок справа - толкаем вправо
                        push_direction = 1
                    
                    if push_direction != 0 and self.carried_by is None and not self.thrown:
                        # Пытаемся толкнуть блок
                        push_speed = max(abs(entity.vx), 2)  # минимум 2 пикселя
                        pushed = self._try_push(push_direction, platforms, push_speed)
                        if pushed:
                            # Если блок сдвинулся, устанавливаем флаг, что блок был толкнут
                            self.has_been_pushed = True
                            # Корректируем позицию сущности, чтобы не было пересечения
                            if dx > 0:
                                entity.rect.right = self.rect.left
                            else:
                                entity.rect.left = self.rect.right
                            # Не обнуляем скорость сущности
                            continue
                        else:
                            # Блок не сдвинулся (упёрся в платформу или другой блок)
                            # Тогда блок действует как твёрдая стена
                            if dx > 0:
                                entity.rect.right = self.rect.left
                                if hasattr(entity, 'vx'):
                                    entity.vx = min(entity.vx, 0)
                            else:
                                entity.rect.left = self.rect.right
                                if hasattr(entity, 'vx'):
                                    entity.vx = max(entity.vx, 0)
                    else:
                        # Сущность не толкает (стоит или движется в другую сторону)
                        # Блок действует как твёрдая стена
                        if dx > 0:
                            entity.rect.right = self.rect.left
                            if hasattr(entity, 'vx'):
                                entity.vx = min(entity.vx, 0)
                        else:
                            entity.rect.left = self.rect.right
                            if hasattr(entity, 'vx'):
                                entity.vx = max(entity.vx, 0)
                else:
                    # Вертикальное перекрытие
                    if dy > 0:
                        # Блок ниже сущности (сущность сверху) - сущность стоит на блоке
                        entity.rect.bottom = self.rect.top
                        if hasattr(entity, 'vy'):
                            # Если блок ещё не был толкнут и не вертикальный, не позволяем сущности стоять на нём
                            if not self.has_been_pushed and not self.is_vertical:
                                # Не обнуляем вертикальную скорость, чтобы сущность продолжала падать
                                # Но позиция уже скорректирована, поэтому добавим горизонтальное смещение для соскальзывания
                                if hasattr(entity, 'vx'):
                                    # Сдвигаем сущность в сторону движения, если она движется
                                    if entity.vx > 0:
                                        entity.rect.x += 1
                                    elif entity.vx < 0:
                                        entity.rect.x -= 1
                                    # Если стоит на месте, не смещаем
                                # Не устанавливаем on_ground
                            else:
                                entity.vy = 0
                                if hasattr(entity, 'on_ground'):
                                    entity.on_ground = True
                    else:
                        # Блок выше сущности (сущность снизу)
                        # Определяем вертикальную скорость блока
                        vertical_velocity = self.throw_vy if self.thrown else self.vy
                        
                        # Проверяем, движется ли блок вниз (падает на сущность)
                        if vertical_velocity > 0 and self.carried_by is None:
                            # Блок падает на сущность - приземляем блок на сущность
                            self.rect.bottom = entity.rect.top
                            if self.thrown:
                                self.thrown = False  # прекращаем бросок
                                self.throw_vx = 0
                                self.throw_vy = 0
                            else:
                                self.vy = 0
                            self.on_ground = True  # блок стоит на сущности
                        else:
                            # Блок стоит или движется вверх - сущность подпрыгивает в блок
                            entity.rect.top = self.rect.bottom
                            if hasattr(entity, 'vy'):
                                entity.vy = 0
    
    def _try_push(self, direction, platforms, push_speed=None):
        """
        Попытаться сдвинуть блок в направлении direction (1 вправо, -1 влево).
        Проверяет коллизии с платформами и другими блоками (пока только платформы).
        Возвращает True, если блок сдвинулся, False если упёрся.
        """
        if push_speed is None:
            push_speed = 2  # минимальная скорость толкания
        else:
            # Ограничим максимальную скорость толкания, чтобы не проскакивать сквозь стены
            push_speed = min(push_speed, 5)
            # Убедимся, что скорость не меньше минимальной
            if push_speed < 2:
                push_speed = 2
        
        # Сохраняем исходную позицию
        original_x = self.rect.x
        # Сдвигаем блок на величину push_speed
        self.rect.x += direction * push_speed
        
        # Проверяем коллизии с платформами
        collision = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                collision = True
                break
        
        # Если есть коллизия, возвращаем блок на место
        if collision:
            self.rect.x = original_x
            return False
        # Иначе блок остаётся на новом месте (толкание успешно)
        return True
    
    def pick_up(self, player):
        """Поднять блок игроком"""
        if self.pushable_only:
            return False  # этот блок нельзя поднимать, только толкать
        if self.carried_by is None and not self.thrown:
            self.carried_by = player
            self.thrown = False
            self.on_ground = False  # блок больше не на земле
            self.has_been_pushed = True  # блок был перемещён (толкнут)
            return True
        return False
    
    def throw(self, direction_x, initial_speed=8):
        """Бросить блок в направлении direction_x (1 вправо, -1 влево)"""
        if self.carried_by is not None:
            self.carried_by = None
            self.thrown = True
            self.throw_time = 0
            self.throw_vx = direction_x * initial_speed
            # Начальная вертикальная скорость вверх (бросок по дуге)
            # Коэффициент 1.2 обеспечивает красивую траекторию
            self.throw_vy = -initial_speed * 1.2
            self.on_ground = False  # блок больше не на земле
            return True
        return False


class Button(Entity):
    """Кнопка, которую можно нажимать для открытия/закрытия двери"""
    def __init__(self, x, y, width=40, height=20, image_path=None, door_id=None, toggle=False):
        super().__init__(x, y, width, height, color=(100, 200, 100), image_path=image_path)
        self.pressed = False
        self.door_id = door_id  # ID двери, которую открывает эта кнопка
        self.prev_collision = False  # было ли столкновение в предыдущем кадре
        self.toggle = toggle  # если True, то кнопка работает как рычаг (переключатель)
    
    def update(self, players, doors, blocks=None):
        """Обновление состояния кнопки: проверка коллизии с игроками и блоками"""
        # Проверяем коллизию с каждым игроком
        collision = False
        for player in players:
            if self.rect.colliderect(player.rect):
                collision = True
                break
        
        # Если коллизии с игроками нет, проверяем блоки (если переданы)
        if not collision and blocks is not None:
            for block in blocks:
                # Блок должен быть статичным (не переносится и не брошен)
                if block.carried_by is None and not block.thrown:
                    if self.rect.colliderect(block.rect):
                        collision = True
                        break
        
        # Обработка в зависимости от режима (обычная кнопка или рычаг)
        if self.toggle:
            # Рычаг: переключаем состояние при появлении коллизии (фронт)
            if collision and not self.prev_collision:
                if self.pressed:
                    self.depress(doors)
                else:
                    self.press(doors)
        else:
            # Обычная кнопка: нажимаем при коллизии, отпускаем при её отсутствии
            if collision and not self.pressed:
                self.press(doors)
            elif not collision and self.pressed:
                self.depress(doors)
        
        self.prev_collision = collision
    
    def press(self, doors):
        """Нажать кнопку и открыть связанную дверь"""
        self.pressed = True
        # Не меняем цвет, оставляем изображение как есть
        GameErrorHandler.log_error(f"Button pressed (door_id={self.door_id})", "Button.press", "INFO")
        
        # Открываем все двери с совпадающим door_id
        if self.door_id and doors:
            for door in doors:
                if door.door_id == self.door_id:
                    door.open()
    
    def depress(self, doors):
        """Отпустить кнопку и закрыть связанную дверь"""
        self.pressed = False
        # Не меняем цвет, оставляем изображение как есть
        GameErrorHandler.log_error(f"Button depressed (door_id={self.door_id})", "Button.depress", "INFO")
        
        # Закрываем все двери с совпадающим door_id
        if self.door_id and doors:
            for door in doors:
                if door.door_id == self.door_id:
                    door.close()
    
    def reset(self):
        """Сбросить кнопку в исходное состояние"""
        self.pressed = False
        self.prev_collision = False


class Door(Entity):
    """Дверь, которая открывается при нажатии кнопки"""
    def __init__(self, x, y, width=80, height=20, image_path=None, door_id=None, horizontal=True):
        super().__init__(x, y, width, height, color=(255, 255, 0), image_path=image_path)  # жёлтый цвет
        self.door_id = door_id
        self.horizontal = horizontal
        self.opened = False
        self.open_speed = 5  # скорость открытия/закрытия (пикселей за кадр)
        self.original_x = x
        self.original_y = y
        self.target_x = x  # целевая позиция X (изначально закрыта)
        self.target_y = y  # для вертикального открытия (не используется)
        self.solid = True  # дверь твёрдая
    
    def update(self):
        """Обновление состояния двери: движение к целевой позиции"""
        if self.horizontal:
            # Горизонтальное движение
            if self.opened:
                # Двигаемся к target_x (открытое положение)
                if self.rect.x < self.target_x:
                    self.rect.x += self.open_speed
                    if self.rect.x > self.target_x:
                        self.rect.x = self.target_x
            else:
                # Двигаемся к original_x (закрытое положение)
                if self.rect.x > self.original_x:
                    self.rect.x -= self.open_speed
                    if self.rect.x < self.original_x:
                        self.rect.x = self.original_x
        else:
            # Вертикальное движение
            if self.opened:
                # Двигаемся вверх
                if self.rect.y > self.target_y - self.rect.height:
                    self.rect.y -= self.open_speed
                    if self.rect.y < self.target_y - self.rect.height:
                        self.rect.y = self.target_y - self.rect.height
            else:
                # Двигаемся вниз
                if self.rect.y < self.original_y:
                    self.rect.y += self.open_speed
                    if self.rect.y > self.original_y:
                        self.rect.y = self.original_y
    
    def open(self):
        """Начать открытие двери"""
        self.opened = True
        GameErrorHandler.log_error(f"Door opening (id={self.door_id}, horizontal={self.horizontal})", "Door.open", "INFO")
        # Устанавливаем целевую позицию (на ширину двери вправо)
        if self.horizontal:
            self.target_x = self.original_x + self.rect.width
        else:
            self.target_y = self.original_y - self.rect.height
    
    def close(self):
        """Начать закрытие двери"""
        self.opened = False
        GameErrorHandler.log_error(f"Door closing (id={self.door_id})", "Door.close", "INFO")
        # Целевая позиция - исходная
    
    def is_open(self):
        """Проверка, полностью ли открыта дверь"""
        if self.horizontal:
            return self.rect.x >= self.target_x
        else:
            return self.rect.y <= self.target_y - self.rect.height
    
    def is_closed(self):
        """Проверка, полностью ли закрыта дверь"""
        if self.horizontal:
            return self.rect.x <= self.original_x
        else:
            return self.rect.y >= self.original_y


class MovingBlock(Entity):
    """Блок, который двигается по вертикали при нажатии кнопки"""
    def __init__(self, x, y, width=40, height=40, color=(150, 150, 200), image_path=None,
                 move_speed=3, move_range=200, move_up=False):
        super().__init__(x, y, width, height, color, image_path)
        self.original_y = y
        self.move_speed = move_speed  # скорость движения (пикселей за кадр)
        self.move_range = move_range  # максимальное расстояние движения в пикселях
        self.move_up = move_up  # направление движения: True - вверх, False - вниз
        self.moving = False  # флаг движения
        self.current_offset = 0  # текущее смещение от исходной позиции
        
    def update(self, platforms):
        """Обновление позиции блока"""
        if self.moving:
            # Движение вниз (если move_up=False) или вверх (если move_up=True)
            if not self.move_up:  # движение вниз
                if self.current_offset < self.move_range:
                    self.rect.y += self.move_speed
                    self.current_offset += self.move_speed
            else:  # движение вверх
                if self.current_offset > -self.move_range:
                    self.rect.y -= self.move_speed
                    self.current_offset -= self.move_speed
            
            # Проверяем коллизии с платформами
            self._check_collision(platforms)
        else:
            # Возвращаемся в исходную позицию, если есть смещение
            if self.current_offset != 0:
                if self.current_offset > 0:  # блок ниже исходной позиции
                    # Двигаем вверх
                    self.rect.y -= self.move_speed
                    self.current_offset -= self.move_speed
                    if self.current_offset < 0:
                        # Корректируем, если перешли исходную позицию
                        self.rect.y = self.original_y
                        self.current_offset = 0
                else:  # блок выше исходной позиции (если move_up=True и мы двигались вверх)
                    # Двигаем вниз
                    self.rect.y += self.move_speed
                    self.current_offset += self.move_speed
                    if self.current_offset > 0:
                        self.rect.y = self.original_y
                        self.current_offset = 0
    
    def _check_collision(self, platforms):
        """Проверка столкновений с платформами"""
        # Предполагаем, что блок не на земле, пока не обнаружена коллизия снизу
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Если столкнулись, останавливаем движение в текущем направлении
                self.moving = False
                # Возвращаем на предыдущую позицию
                if not self.move_up:  # двигались вниз
                    self.rect.y -= self.move_speed
                    self.current_offset -= self.move_speed
                else:  # двигались вверх
                    self.rect.y += self.move_speed
                    self.current_offset += self.move_speed
                break
    
    def start_moving(self):
        """Начать движение блока"""
        self.moving = True
    
    def stop_moving(self):
        """Остановить движение блока"""
        self.moving = False
    
    def reset_position(self):
        """Вернуть блок в исходное положение"""
        self.rect.y = self.original_y
        self.current_offset = 0
        self.moving = False


class VerticalButton(Entity):
    """Кнопка для управления вертикальным движением блока"""
    def __init__(self, x, y, width=40, height=20, image_path=None, block_id=None):
        super().__init__(x, y, width, height, color=(200, 100, 200), image_path=image_path)
        self.pressed = False
        self.block_id = block_id  # ID блока, которым управляет кнопка
        self.prev_collision = False  # было ли столкновение в предыдущем кадре
    
    def update(self, players, moving_blocks, blocks=None):
        """Обновление состояния кнопки: проверка коллизии с игроками и блоками"""
        # Проверяем коллизию с каждым игроком
        collision = False
        for player in players:
            if self.rect.colliderect(player.rect):
                collision = True
                break
        
        # Если коллизии с игроками нет, проверяем блоки (если переданы)
        if not collision and blocks is not None:
            for block in blocks:
                # Блок должен быть статичным (не переносится и не брошен)
                if block.carried_by is None and not block.thrown:
                    if self.rect.colliderect(block.rect):
                        collision = True
                        break
        
        # Если коллизия появилась (не было, стало есть) - нажимаем
        if collision and not self.pressed:
            self.press(moving_blocks)
        # Если коллизия исчезла (была, стало нет) - отпускаем
        elif not collision and self.pressed:
            self.depress(moving_blocks)
        
        self.prev_collision = collision
    
    def press(self, moving_blocks):
        """Нажать кнопку и начать движение блока"""
        self.pressed = True
        GameErrorHandler.log_error(f"VerticalButton pressed (block_id={self.block_id})", "VerticalButton.press", "INFO")
        
        # Начинаем движение связанного блока
        if self.block_id and moving_blocks:
            for block in moving_blocks:
                if hasattr(block, 'block_id') and block.block_id == self.block_id:
                    block.start_moving()
                    break
    
    def depress(self, moving_blocks):
        """Отпустить кнопку и остановить движение блока"""
        self.pressed = False
        GameErrorHandler.log_error(f"VerticalButton depressed (block_id={self.block_id})", "VerticalButton.depress", "INFO")
        
        # Останавливаем движение связанного блока
        if self.block_id and moving_blocks:
            for block in moving_blocks:
                if hasattr(block, 'block_id') and block.block_id == self.block_id:
                    block.stop_moving()
                    break
    
    def reset(self):
        """Сбросить кнопку в исходное состояние"""
        self.pressed = False
        self.prev_collision = False


class Collectible(Entity):
    """Собираемый элемент, исчезает при касании игрока"""
    def __init__(self, x, y, width=50, height=50, image_path=None, color=(255, 255, 0), item_id=None):
        super().__init__(x, y, width, height, color, image_path)
        self.collected = False
        self.item_id = item_id  # уникальный идентификатор элемента
    
    def update(self, players):
        """Обновление состояния: проверка коллизии с любым игроком"""
        if self.collected:
            return
        for player in players:
            if self.rect.colliderect(player.rect):
                self.collected = True
                self.kill()  # удаляем из всех групп
                break
    
    def draw(self, screen):
        """Отрисовка элемента, если не собран"""
        if not self.collected:
            screen.blit(self.image, self.rect)


class DoorExit(Entity):
    """Дверь выхода, активируется при одновременном присутствии Аделины и Ани в зоне"""
    def __init__(self, x, y, width=100, height=150, image_path=None, screen_width=1280, screen_height=720):
        # Используем изображение door_exit.png из папки image/sprite/
        if image_path is None:
            image_path = "image/sprite/door_exit.png"
        super().__init__(x, y, width, height, color=(200, 100, 50), image_path=image_path)
        self.activated = False
        self.activation_zone = pygame.Rect(x - 50, y - 30, width + 100, height + 60)  # зона активации больше самой двери
        self.fade_alpha = 0  # прозрачность затемнения (0-255)
        self.fade_speed = 5  # скорость затемнения
        self.level_complete = False
        self.stats_shown = False
        self.collected_items = 0
        self.total_items = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui = None  # LevelCompleteUI будет создан при активации
        self.ui_result = None  # результат выбора кнопки
    
    def update(self, players, collected_items=0, total_items=0):
        """Обновление состояния двери: проверка активации"""
        if self.activated or self.level_complete:
            return
        
        # Обновляем статистику
        self.collected_items = collected_items
        self.total_items = total_items
        
        # Проверяем, находятся ли оба персонажа в зоне активации
        adelina_in_zone = False
        anya_in_zone = False
        
        for player in players:
            # Определяем имя персонажа по цвету или другим характеристикам
            # В текущей реализации имена не хранятся, поэтому используем цвет как идентификатор
            # Аделина - BLUE (0, 100, 255), Аня - RED (255, 100, 100)
            if hasattr(player, 'color'):
                if player.color == (0, 100, 255):  # BLUE - Аделина
                    if self.activation_zone.colliderect(player.rect):
                        adelina_in_zone = True
                elif player.color == (255, 100, 100):  # RED - Аня
                    if self.activation_zone.colliderect(player.rect):
                        anya_in_zone = True
        
        # Если оба персонажа в зоне - активируем дверь
        if adelina_in_zone and anya_in_zone and not self.activated:
            self.activated = True
            self.start_level_completion()
    
    def start_level_completion(self):
        """Начинает процесс завершения уровня, создаёт UI с кнопками"""
        self.level_complete = True
        # Создаём UI завершения уровня
        self.ui = LevelCompleteUI(self.screen_width, self.screen_height)
        self.ui.set_stats(self.collected_items, self.total_items)
        self.ui.visible = True
        # ui_result будет установлен после нажатия кнопки
        self.ui_result = None
        # Здесь можно добавить звук или анимацию
    
    def update_fade(self):
        """Обновление плавного затемнения экрана"""
        if self.level_complete and self.fade_alpha < 255:
            self.fade_alpha += self.fade_speed
            if self.fade_alpha > 255:
                self.fade_alpha = 255
    
    def draw_fade(self, screen):
        """Отрисовка затемнения поверх экрана"""
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface((screen.get_width(), screen.get_height()))
            fade_surface.set_alpha(self.fade_alpha)
            fade_surface.fill((0, 0, 0))
            screen.blit(fade_surface, (0, 0))
    
    def handle_events(self, events):
        """Обработка событий для UI завершения уровня"""
        if self.ui is not None and self.ui.visible:
            result = self.ui.update(events)
            if result is not None:
                self.ui_result = result
                return result
        return None
    
    def update_ui(self):
        """Обновление UI (вызывается каждый кадр)"""
        # Анимация затемнения больше не нужна, UI рисует свой фон
        pass
    
    def draw_ui(self, screen):
        """Отрисовка UI завершения уровня"""
        if self.ui is not None and self.ui.visible:
            # UI сам рисует фон
            self.ui.draw(screen)
    
    def draw(self, screen):
        """Отрисовка двери"""
        screen.blit(self.image, self.rect)
        # Для отладки можно нарисовать зону активации
        # pygame.draw.rect(screen, (255, 0, 0), self.activation_zone, 2)


class LevelCompleteUI:
    """Интерфейс завершения уровня: три кнопки горизонтально"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        
        # Фоновое изображение win.jpg
        self.background = load_image("image/sprite/win.jpg", screen_width, screen_height)
        
        # Статистика (можно скрыть)
        self.collected_items = 0
        self.total_items = 0
        
        # Параметры кнопок
        self.button_width = 400
        self.button_height = 250
        self.button_gap = 20
        self.button_color = (100, 200, 100)
        self.button_hover_color = (50, 180, 50)
        self.button_text_color = (255, 255, 255)
        
        # Вычисляем позиции для трёх кнопок горизонтально по центру
        total_width = 3 * self.button_width + 2 * self.button_gap
        start_x = (screen_width - total_width) // 2
        button_y = screen_height // 2 + 50
        
        # Создаём прямоугольники кнопок
        self.button_menu = pygame.Rect(start_x, button_y, self.button_width, self.button_height)
        self.button_restart = pygame.Rect(start_x + self.button_width + self.button_gap, button_y, self.button_width, self.button_height)
        self.button_continue = pygame.Rect(start_x + 2 * (self.button_width + self.button_gap), button_y, self.button_width, self.button_height)
        
        # Загружаем изображения кнопок
        self.button_menu_image = load_image("image/sprite/button_menu.jpg", self.button_width, self.button_height)
        self.button_restart_image = load_image("image/sprite/button_replay.jpg", self.button_width, self.button_height)
        self.button_continue_image = load_image("image/sprite/button_next.jpg", self.button_width, self.button_height)
        
        # Тексты больше не используются
        self.menu_text = None
        self.restart_text = None
        self.continue_text = None
        
        # Статистика (можно скрыть)
        self.stats_text = None
        self.stats_rect = None
        
        self.visible = False
    
    def set_stats(self, collected, total):
        """Установить статистику собранных предметов"""
        self.collected_items = collected
        self.total_items = total
        self.stats_text = self.font_medium.render(
            f"Собрано предметов: {collected} / {total}",
            True,
            (255, 255, 255)
        )
        self.stats_rect = self.stats_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 30))
    
    def update(self, events):
        """Обновление UI: обработка событий мыши"""
        if not self.visible:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_menu.collidepoint(event.pos):
                    return "menu"
                elif self.button_restart.collidepoint(event.pos):
                    return "restart"
                elif self.button_continue.collidepoint(event.pos):
                    return "continue"
        return None
    
    def draw(self, screen):
        """Отрисовка интерфейса"""
        if not self.visible:
            return
        
        # Фон win.jpg
        screen.blit(self.background, (0, 0))
        
        # Статистика (если есть)
        if self.stats_text:
            screen.blit(self.stats_text, self.stats_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка "Меню"
        screen.blit(self.button_menu_image, self.button_menu)
        if self.button_menu.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.button_menu, 1, border_radius=10)
        
        # Кнопка "Заново"
        screen.blit(self.button_restart_image, self.button_restart)
        if self.button_restart.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.button_restart, 1, border_radius=10)
        
        # Кнопка "Продолжить"
        screen.blit(self.button_continue_image, self.button_continue)
        if self.button_continue.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.button_continue, 1, border_radius=10)


class LevelFailUI:
    """Интерфейс проигрыша: две кнопки горизонтально"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_medium = pygame.font.Font(None, 40)
        
        # Фоновое изображение failed.jpg
        self.background = load_image("image/sprite/failed.jpg", screen_width, screen_height)
        
        # Параметры кнопок
        self.button_width = 400
        self.button_height = 250
        self.button_gap = 20
        self.button_color = (200, 100, 100)  # красноватый цвет для проигрыша
        self.button_hover_color = (180, 50, 50)
        self.button_text_color = (255, 255, 255)
        
        # Вычисляем позиции для двух кнопок горизонтально по центру
        total_width = 2 * self.button_width + self.button_gap
        start_x = (screen_width - total_width) // 2
        button_y = screen_height // 2 + 50
        
        # Создаём прямоугольники кнопок
        self.button_menu = pygame.Rect(start_x, button_y, self.button_width, self.button_height)
        self.button_restart = pygame.Rect(start_x + self.button_width + self.button_gap, button_y, self.button_width, self.button_height)
        
        # Загружаем изображения кнопок
        self.button_menu_image = load_image("image/sprite/button_menu.jpg", self.button_width, self.button_height)
        self.button_restart_image = load_image("image/sprite/button_replay.jpg", self.button_width, self.button_height)
        
        # Тексты больше не используются
        self.menu_text = None
        self.restart_text = None
        
        self.visible = False
    
    def update(self, events):
        """Обновление UI: обработка событий мыши"""
        if not self.visible:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_menu.collidepoint(event.pos):
                    return "menu"
                elif self.button_restart.collidepoint(event.pos):
                    return "restart"
        return None
    
    def draw(self, screen):
        """Отрисовка интерфейса"""
        if not self.visible:
            return
        
        # Фон failed.jpg
        screen.blit(self.background, (0, 0))
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка "Меню"
        screen.blit(self.button_menu_image, self.button_menu)
        if self.button_menu.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.button_menu, 1, border_radius=10)
        
        # Кнопка "Начать заново"
        screen.blit(self.button_restart_image, self.button_restart)
        if self.button_restart.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.button_restart, 1, border_radius=10)


#         dy_anya = anya_speed


# # Проверка столкновение игрока со стеной
#     anya_rect.x += dx_anya
#     anya_rect.y += dy_anya
#     if anya_rect.colliderect(wall_rect):
#         anya_rect.x -= dx_anya
#         anya_rect.y -= dy_anya
         
#     # Проверка столкновение игрока со стеной
#     adeline_rect.x += dx_adeline
#     adeline_rect.y += dy_adeline
#     if adeline_rect.colliderect(wall_rect):
#         adeline_rect.x -= dx_adeline
#         adeline_rect.y -= dy_adeline
         
         



# # Черноскутов (первый преподаватель)
# teacher1_rect = pygame.Rect(200, 200, 40, 40)
# teacher1_color = (150, 0, 0)  # Тёмно-красный
# teacher1_speed = 2
# teacher1_patrol = [(200, 200), (500, 200)]
# teacher1_patrol_index = 0
# teacher1_state = "patrol"
# teacher1_chase_target = None

# # Мухлынин (второй преподаватель) 
# teacher2_rect = pygame.Rect(600, 400, 40, 40)
# teacher2_color = (150, 50, 0)  # Коричнево-красный
# teacher2_speed = 3  # Чуть быстрее первого
# teacher2_patrol = [(600, 400), (600, 100)]  # Ходит вертикально
# teacher2_target = 0
# teacher2_patrol_index = 0
# teacher2_state = "patrol"
# teacher2_chase_target = None
# # Состояния преподавателей: "patrol" (патруль) или "chase" (преследование)

# # Кого преследуют (None если никого)
# teacher1_target = None
# teacher2_target = None

