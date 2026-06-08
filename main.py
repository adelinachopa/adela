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
from entities import LevelFailUI
import save_manager


def main():
    # Инициализация PyGame с проверкой
    # pygame.init() возвращает кортеж (n_success, n_failed)
    init_result = pygame.init()
    if init_result[1] > 0:
        print(f"FATAL ERROR: PyGame initialization failed! ({init_result[1]} modules failed)")
        return 1
    
    # Проверка инициализации модулей
    if not pygame.font.get_init():
        print("WARNING: Font module not initialized properly")
        pygame.font.init()
    
    # Импортируем setting для возможности переопределения констант
    import setting as s
    
    # Создаём полноэкранное окно
    try:
        screen = pygame.display.set_mode(
            (s.SCREEN_WIDTH, s.SCREEN_HEIGHT),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
    except pygame.error as e:
        print(f"ERROR: Failed to create display: {e}")
        print("Trying windowed mode instead...")
        try:
            screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
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
        background = load_image(BACKGROUND_IMG, s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        # Сохраняем начальное количество собираемых элементов
        initial_collectibles_count = len(level.collectibles)

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

                # Проверка столкновений игроков с врагами
                if not level_failed and level.check_collisions():
                    print("Игрок столкнулся с врагом! Игра окончена.")
                    level_failed = True
                    level_fail_ui = LevelFailUI(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
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
                indicator_x = s.SCREEN_WIDTH - 200
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
