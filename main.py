# #основной файл, где происходит основные обработки
import pygame
import sys
import json
import os
import random
import re
from setting import *
from levels import Level
from menu import Menu
from level_select import LevelSelect
from error_handler import GameErrorHandler
from joystick import create_mobile_controls
from entities import LevelFailUI
import save_manager

def generate_level_from_template(template_path="levels/level_01.json", level_num=1):
    """
    Генерирует новый уровень на основе шаблона.
    Возвращает dict с данными уровня.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки шаблона {template_path}: {e}")
        # Возвращаем данные по умолчанию
        from level_loader import LevelLoader
        return LevelLoader.get_default_level()
    
    # Изменяем метаданные
    data["metadata"]["id"] = f"generated_{level_num}"
    data["metadata"]["name"] = f"Сгенерированный уровень {level_num}"
    data["metadata"]["description"] = f"Автоматически сгенерированный уровень на основе {os.path.basename(template_path)}"
    
    # Случайное смещение по X для всех объектов (кроме тех, которые должны остаться на месте)
    offset_x = random.randint(-100, 100)  # от -100 до +100 пикселей
    offset_y = random.randint(-50, 50)   # небольшое смещение по Y
    
    # Функция для сдвига координат в списке объектов
    def shift_coords(obj_list, keys=('x', 'y')):
        for obj in obj_list:
            for key in keys:
                if key in obj:
                    obj[key] += offset_x if key == 'x' else offset_y
                    # Ограничим, чтобы не уходить за границы экрана (ширина 1280, высота 720)
                    if key == 'x':
                        if obj[key] < 0:
                            obj[key] = 0
                        elif obj[key] > 1200:
                            obj[key] = 1200
                    if key == 'y':
                        if obj[key] < 0:
                            obj[key] = 0
                        elif obj[key] > 700:
                            obj[key] = 700
    
    # Сдвигаем платформы
    if "platforms" in data:
        shift_coords(data["platforms"])
    
    # Сдвигаем игроков (но оставим их близко к началу)
    if "players" in data:
        for player in data["players"]:
            player["x"] += offset_x // 2  # меньшее смещение для игроков
            player["y"] += offset_y // 2
    
    # Сдвигаем врагов
    if "enemies" in data:
        shift_coords(data["enemies"])
    
    # Сдвигаем блоки
    if "blocks" in data:
        shift_coords(data["blocks"])
    
    # Сдвигаем кнопки
    if "buttons" in data:
        shift_coords(data["buttons"])
    
    # Сдвигаем двери
    if "doors" in data:
        shift_coords(data["doors"])
    
    # Сдвигаем собираемые предметы
    if "collectibles" in data:
        shift_coords(data["collectibles"])
    
    # Сдвигаем движущиеся блоки
    if "moving_blocks" in data:
        shift_coords(data["moving_blocks"])
    
    # Сдвигаем вертикальные кнопки
    if "vertical_buttons" in data:
        shift_coords(data["vertical_buttons"])
    
    # Сдвигаем двери выхода
    if "door_exits" in data:
        shift_coords(data["door_exits"])
    
    # Сдвигаем цели (goals)
    if "goals" in data and isinstance(data["goals"], dict):
        if "x" in data["goals"]:
            data["goals"]["x"] += offset_x
        if "y" in data["goals"]:
            data["goals"]["y"] += offset_y
    
    # Возвращаем модифицированные данные
    return data

def main():
    # Инициализация PyGame с проверкой
    if not pygame.init():
        print("FATAL ERROR: PyGame initialization failed!")
        return 1
    
    # Проверка инициализации модулей
    modules_ok = True
    
    if not pygame.display.get_init():
        print("WARNING: Display module not initialized properly")
        modules_ok = False
    
    if not pygame.font.get_init():
        print("WARNING: Font module not initialized properly")
        # Попытка инициализировать вручную
        pygame.font.init()
    
    if not modules_ok:
        print("WARNING: Some PyGame modules failed to initialize")
        # Можно продолжить, но с ограниченной функциональностью
    
    # Создаём полноэкранное окно с масштабированием
    try:
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.FULLSCREEN | pygame.SCALED
        )
    except pygame.error as e:
        print(f"ERROR: Failed to create display: {e}")
        print("Trying windowed mode instead...")
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e2:
            print(f"FATAL: Could not create any display: {e2}")
            pygame.quit()
            return 1
    
    pygame.display.set_caption("Escape to EMK - Platformer")
    clock = pygame.time.Clock()
    
    # Внешний цикл: меню -> игра -> меню
    while True:
        # Запускаем меню
        menu = Menu(screen)
        if not menu.run():
            # Пользователь хочет выйти из игры
            pygame.quit()
            sys.exit()
        
        # Экран выбора уровней
        level_select = LevelSelect(screen)
        level_file = level_select.run()
        if level_file is None:  # выход из игры
            pygame.quit()
            sys.exit()
        if level_file == "back":  # вернуться в меню
            continue
        
        # Загрузка выбранного уровня
        level = Level(level_file)
        current_level_path = level_file  # сохраняем путь для перезагрузки
        # Извлекаем идентификатор уровня (имя файла без расширения)
        level_id = os.path.splitext(os.path.basename(current_level_path))[0]
        print(f"Уровень загружен из: {level.level_source}")
        # После создания screen
        background = load_image(BACKGROUND_IMG, SCREEN_WIDTH, SCREEN_HEIGHT)
        # Сохраняем начальное количество собираемых элементов
        initial_collectibles_count = len(level.collectibles)
        
        # Инициализация мобильного управления (если нужно)
        mobile_controls = None
        if IS_MOBILE:
            mobile_controls = create_mobile_controls()
            print("Мобильное управление активировано")

        # Загрузка изображения кнопки перезапуска уровня
        restart_button_image = load_image("image/sprite/refresh.jpg", 100, 100)
        restart_button_rect = restart_button_image.get_rect(topleft=(20, 20))

        running = True
        level_complete = False
        level_failed = False
        active_door_exit = None
        level_fail_ui = None
        quit_game = False  # флаг для выхода из игры полностью
        try:
            while running:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        quit_game = True
                        running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False  # возврат в меню
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # левая кнопка мыши
                        if not level_complete and not level_failed and restart_button_rect.collidepoint(event.pos):
                            print("Перезапуск уровня по нажатию кнопки...")
                            # Перезагружаем текущий уровень
                            level = Level(current_level_path)
                            print(f"Уровень загружен из: {level.level_source}")
                            initial_collectibles_count = len(level.collectibles)
                            # Сбрасываем состояние завершения уровня и проигрыша
                            level_complete = False
                            level_failed = False
                            active_door_exit = None
                            level_fail_ui = None

                # Обработка ввода
                keys = pygame.key.get_pressed()
                
                # Если есть мобильное управление, получаем состояние от него
                if mobile_controls:
                    mobile_keys = mobile_controls.handle_events(events)
                    # Объединяем состояния клавиш (мобильные имеют приоритет)
                    for key, pressed in mobile_keys.items():
                        # Эмулируем нажатие клавиш
                        # В Pygame нет прямого способа изменить pygame.key.get_pressed(),
                        # поэтому создаем свой словарь состояний
                        keys = list(keys)  # Конвертируем в список для модификации
                        if key < len(keys):
                            keys[key] = pressed
                    # Конвертируем обратно в нужный формат
                    # Создаем новый объект, эмулирующий pygame.key.get_pressed()
                    class KeyState:
                        def __getitem__(self, key):
                            if key < len(keys):
                                return keys[key]
                            return False
                    
                    key_state = KeyState()
                else:
                    key_state = keys

                if not level_complete and not level_failed:
                    for player in level.players:
                        player.handle_input(key_state)
                        player.handle_block_interaction(key_state, level.blocks)

                level.update(level_complete=level_complete, level_failed=level_failed)

                # Проверка завершения уровня (активация двери выхода)
                if not level_complete and not level_failed:
                    for door_exit in level.door_exits:
                        if door_exit.level_complete:
                            level_complete = True
                            active_door_exit = door_exit
                            # Сохраняем прогресс уровня
                            collected = initial_collectibles_count - len(level.collectibles)
                            total = initial_collectibles_count
                            # Используем уже вычисленный идентификатор уровня
                            save_manager.update_level_progress(level_id, True, collected, total)
                            print(f"Уровень {level_id} завершён! Собрано {collected}/{total} питончиков.")
                            break

                # Отладочный вывод состояния игроков
                for i, player in enumerate(level.players):
                    GameErrorHandler.log_error(
                        f"Player {i}: rect={player.rect}, vx={player.vx}, vy={player.vy}, on_ground={player.on_ground if hasattr(player, 'on_ground') else 'N/A'}",
                        "main.game_loop",
                        "DEBUG"
                    )

                # Проверка столкновений игроков с врагами
                if not level_failed and level.check_collisions():
                    print("Игрок столкнулся с врагом! Игра окончена.")
                    level_failed = True
                    level_fail_ui = LevelFailUI(SCREEN_WIDTH, SCREEN_HEIGHT)
                    level_fail_ui.visible = True
                    # Сохраняем прогресс уровня (проигрыш)
                    collected = initial_collectibles_count - len(level.collectibles)
                    total = initial_collectibles_count
                    save_manager.update_level_progress(level_id, False, collected, total)
                    print(f"Уровень {level_id} провален. Собрано {collected}/{total} питончиков.")

                # Обработка UI завершения уровня
                if level_complete and active_door_exit is not None:
                    # Проверяем, есть ли уже результат (например, автоматический выход в меню)
                    if active_door_exit.ui_result is not None:
                        ui_result = active_door_exit.ui_result
                    else:
                        ui_result = active_door_exit.handle_events(events)
                    if ui_result is not None:
                        print(f"UI результат: {ui_result}")
                        if ui_result == "menu":
                            print("Возврат в главное меню...")
                            running = False
                        elif ui_result == "restart":
                            print("Перезапуск уровня...")
                            # Перезагружаем текущий уровень
                            level = Level(current_level_path)
                            print(f"Уровень загружен из: {level.level_source}")
                            initial_collectibles_count = len(level.collectibles)
                            # Сбрасываем состояние завершения уровня
                            level_complete = False
                            active_door_exit = None
                            # Продолжаем игровой цикл
                        elif ui_result == "continue":
                            print("Продолжение игры...")
                            # Определяем следующий уровень на основе текущего
                            current_filename = os.path.basename(current_level_path)
                            # Ищем номер в имени файла
                            match = re.search(r'level_?(\d+)', current_filename)
                            if match:
                                current_num = int(match.group(1))
                                next_num = current_num + 1
                                # Пробуем разные форматы имен
                                possible_paths = [
                                    f"levels/level_{next_num}.json",
                                    f"levels/level_{next_num:02d}.json",
                                    f"levels/level_{next_num:02}.json",
                                ]
                                next_level_path = None
                                for path in possible_paths:
                                    if os.path.exists(path):
                                        next_level_path = path
                                        break
                                if next_level_path:
                                    print(f"Загрузка следующего уровня: {next_level_path}")
                                    level = Level(next_level_path)
                                    current_level_path = next_level_path
                                    level_id = os.path.splitext(os.path.basename(current_level_path))[0]
                                else:
                                    print("Следующий уровень не найден. Возврат в меню.")
                                    running = False
                                    continue
                            else:
                                # Если не удалось извлечь номер, загружаем уровень 2 как запасной вариант
                                print("Не удалось определить номер уровня. Загружаем уровень 2...")
                                level = Level("levels/level_2.json")
                                current_level_path = "levels/level_2.json"
                                level_id = "level_2"
                            
                            print(f"Уровень загружен из: {level.level_source}")
                            initial_collectibles_count = len(level.collectibles)
                            # Сбрасываем состояние завершения уровня
                            level_complete = False
                            active_door_exit = None
                            # Продолжаем игровой цикл
                        else:
                            # Неизвестный результат, выходим в меню для безопасности
                            running = False

                # Обработка UI проигрыша
                if level_failed and level_fail_ui is not None:
                    ui_result = level_fail_ui.update(events)
                    if ui_result is not None:
                        print(f"UI результат проигрыша: {ui_result}")
                        if ui_result == "menu":
                            print("Возврат в главное меню...")
                            running = False
                        elif ui_result == "restart":
                            print("Перезапуск уровня...")
                            # Перезагружаем текущий уровень
                            level = Level(current_level_path)
                            print(f"Уровень загружен из: {level.level_source}")
                            initial_collectibles_count = len(level.collectibles)
                            # Сбрасываем состояние проигрыша
                            level_failed = False
                            level_fail_ui = None
                            # Продолжаем игровой цикл

                screen.blit(background, (0, 0))
                level.draw(screen)
                
                # Отрисовка индикатора коллекции в правом верхнем углу
                total_collectibles = initial_collectibles_count
                collected = total_collectibles - len(level.collectibles)
                # Позиция индикатора
                indicator_x = SCREEN_WIDTH - 200
                indicator_y = 20
                # Фон индикатора
                pygame.draw.rect(screen, (50, 50, 50), (indicator_x - 10, indicator_y - 10, 190, 60), border_radius=10)
                # Текст
                font = pygame.font.Font(None, 36)
                text = font.render(f"Собрано: {collected}/{total_collectibles}", True, (255, 255, 255))
                screen.blit(text, (indicator_x, indicator_y))
                # Иконки собранных элементов (просто кружки)
                icon_size = 30
                for i in range(total_collectibles):
                    icon_x = indicator_x + i * (icon_size + 5)
                    icon_y = indicator_y + 40
                    if i < collected:
                        color = (0, 255, 0)  # зелёный - собран
                    else:
                        color = (100, 100, 100)  # серый - не собран
                    pygame.draw.circle(screen, color, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2)
                
                # Отрисовка кнопки перезапуска уровня
                screen.blit(restart_button_image, restart_button_rect)

                # Отрисовка UI завершения уровня (если активно)
                if level_complete and active_door_exit is not None:
                    active_door_exit.draw_ui(screen)
                
                # Отрисовка UI проигрыша (если активно)
                if level_failed and level_fail_ui is not None:
                    level_fail_ui.draw(screen)
                
                # Отрисовка мобильного управления (если активно)
                if mobile_controls:
                    mobile_controls.draw(screen)
                
                pygame.display.flip()
                clock.tick(FPS)
        except Exception as e:
            GameErrorHandler.log_error(f"Game loop error: {e}", "main.game_loop", "ERROR")
            quit_game = True
            running = False

        # После выхода из игрового цикла проверяем, нужно ли завершить игру полностью
        if quit_game:
            pygame.quit()
            sys.exit()
        # Иначе возвращаемся в меню (внешний цикл продолжается)

if __name__ == "__main__":
    main()

















































# import pygame
# from setting import *
# from entities import *
# from bots import *
# from levels import *
# import sys

# # Инициализация Pygame
# pygame.init()



# # Получаем информацию о текущем дисплее
# info = pygame.display.Info()
# screen_width = info.current_w
# screen_height = info.current_h

# screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
# pygame.display.set_caption("Escape to EMK")
# clock = pygame.time.Clock()



# # Игровой цикл 
# running = True
# while running:
#     # 1. Обрабатываем события (закрытие окна, нажатия клавиш)
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         if event.type == pygame.KEYDOWN:
#             if event.key == pygame.K_ESCAPE:
#                 running = False
    
#     # 2. Очищаем экран (заливаем чёрным)
#     # Получаем состояние всех клавиш
#     walk(keys = pygame.key.get_pressed())

# # --- ДВИЖЕНИЕ ПЕРВОГО ПРЕПОДАВАТЕЛЯ ---
#     if teacher1_state == "patrol":
#     # Патрулирование как раньше
#         target1_x, target1_y = teacher1_patrol[teacher1_patrol_index]
    
#         if teacher1_rect.x < target1_x:
#             teacher1_rect.x += teacher1_speed
#         elif teacher1_rect.x > target1_x:
#             teacher1_rect.x -= teacher1_speed
    
#         if teacher1_rect.y < target1_y:
#             teacher1_rect.y += teacher1_speed
#         elif teacher1_rect.y > target1_y:
#             teacher1_rect.y -= teacher1_speed
    
#         if abs(teacher1_rect.x - target1_x) < teacher1_speed and abs(teacher1_rect.y - target1_y) < teacher1_speed:
#             teacher1_patrol_index = 1 - teacher1_patrol_index

#     elif teacher1_state == "chase":
#     # Преследование цели
#         if teacher1_target:
#             if teacher1_rect.x < teacher1_target.centerx:
#                 teacher1_rect.x += teacher1_speed
#             elif teacher1_rect.x > teacher1_target.centerx:
#                 teacher1_rect.x -= teacher1_speed

#             if teacher1_rect.y < teacher1_target.centery:
#                 teacher1_rect.y += teacher1_speed
#             elif teacher1_rect.y > teacher1_target.centery:
#                 teacher1_rect.y -= teacher1_speed

# # --- ДВИЖЕНИЕ ВТОРОГО ПРЕПОДАВАТЕЛЯ ---
#     if teacher2_state == "patrol":
#         target2_x, target2_y = teacher2_patrol[teacher2_patrol_index]
    
#         if teacher2_rect.x < target2_x:
#             teacher2_rect.x += teacher2_speed
#         elif teacher2_rect.x > target2_x:
#             teacher2_rect.x -= teacher2_speed
    
#         if teacher2_rect.y < target2_y:
#             teacher2_rect.y += teacher2_speed
#         elif teacher2_rect.y > target2_y:
#             teacher2_rect.y -= teacher2_speed
    
#         if abs(teacher2_rect.x - target2_x) < teacher2_speed and abs(teacher2_rect.y - target2_y) < teacher2_speed:
#             teacher2_patrol_index = 1 - teacher2_patrol_index

#     elif teacher2_state == "chase":
#         if teacher2_target:
#             if teacher2_rect.x < teacher2_target.centerx:
#                 teacher2_rect.x += teacher2_speed
#             elif teacher2_rect.x > teacher2_target.centerx:
#                 teacher2_rect.x -= teacher2_speed
        
#             if teacher2_rect.y < teacher2_target.centery:
#                 teacher2_rect.y += teacher2_speed
#             elif teacher2_rect.y > teacher2_target.centery:
#                 teacher2_rect.y -= teacher2_speed
# # Список игроков
# #ПРОВЕРКА ОБНАРУЖЕНИЯ И СМЕНА СОСТОЯНИЙ 
#     players = [adeline_rect, anya_rect]

# # Для первого преподавателя
#     teacher1_was_chasing = (teacher1_state == "chase")
#     teacher1_state = "patrol"  # Сначала сбрасываем
#     teacher1_target = None

#     for player in players:
#         dx = teacher1_rect.centerx - player.centerx
#         dy = teacher1_rect.centery - player.centery
#         distance = (dx**2 + dy**2)**0.5
    
#         if distance < 250:  # Увидел игрока
#             teacher1_state = "chase"
#             teacher1_target = player
#             if not teacher1_was_chasing:
#                 who = "Аделину" if player == adeline_rect else "Аню"
#                 print(f"Черноскутов погнался за {who}!")

#     # Если никого не видит, но только что преследовал
#     if teacher1_state == "patrol" and teacher1_was_chasing:
#         print("Черноскутов потерял игрока и вернулся в патруль")

#     # Для второго преподавателя
#     teacher2_was_chasing = (teacher2_state == "chase")
#     teacher2_state = "patrol"
#     teacher2_target = None

#     for player in players:
#         dx = teacher2_rect.centerx - player.centerx
#         dy = teacher2_rect.centery - player.centery
#         distance = (dx**2 + dy**2)**0.5
    
#         if distance < 250:
#             teacher2_state = "chase"
#             teacher2_target = player
#             if not teacher2_was_chasing:
#                 who = "Аделину" if player == adeline_rect else "Аню"
#                 print(f"Мухлынин погнался за {who}!")
#     if teacher2_state == "patrol" and teacher2_was_chasing:
#         print("Мухлынин потерял игрока и вернулся в патруль")

    

#     screen.fill(BLACK)
#     # Визуализация радиусов обнаружения (временная отладка)
#     pygame.draw.circle(screen, (255, 0, 0), teacher1_rect.center, 250, 1)  # Красный круг
#     pygame.draw.circle(screen, (255, 100, 0), teacher2_rect.center, 250, 1)  # Оранжевый круг
#     # 3. Здесь будет отрисовка всех объектов
#     # Рисуем игрока
#     pygame.draw.rect(screen, GREEN, wall_rect)

#     pygame.draw.rect(screen, teacher1_color, teacher1_rect)  # Черноскутов
#     pygame.draw.rect(screen, teacher2_color, teacher2_rect) #Мухлынин
#     pygame.draw.rect(screen, adeline_color, adeline_rect) # Аделина
#     pygame.draw.rect(screen, anya_color, anya_rect) # Аня


#     # 4. Обновляем экран
#     # screen.fill((0, 128, 255))
#     pygame.display.flip()
    
#     # 5. Контроль FPS (кадров в секунду)
#     clock.tick(60)
# pygame.quit()
# sys.exit()


