import pygame
import random
import json
import os
import sys
import time
import math

pygame.init()

# ============================================================
# CODE BREAKER — polished main.py
# Исправлено: F11, fullscreen, масштабирование интерфейса,
# обрезка текста, сохранения, визуал, кнопки и стабильность.
# ============================================================

BASE_WIDTH = 1200
BASE_HEIGHT = 720
WINDOWED_SIZE = (BASE_WIDTH, BASE_HEIGHT)
MIN_WINDOW_SIZE = (900, 540)
FPS = 60

SAVE_FILE = "save_data.json"
NEXT_LEVEL_EVENT = pygame.USEREVENT + 10

BLACK = (5, 8, 12)
DARK = (10, 18, 24)
DARK_2 = (8, 14, 20)
PANEL = (18, 36, 48)
PANEL_HOVER = (20, 55, 60)
GREEN = (0, 255, 120)
GREEN_DARK = (0, 150, 80)
GREEN_MUTED = (0, 95, 62)
CYAN = (0, 220, 255)
CYAN_DARK = (0, 125, 160)
RED = (255, 70, 80)
YELLOW = (255, 220, 80)
WHITE = (230, 240, 240)
GRAY = (130, 150, 150)
GRAY_DARK = (70, 90, 95)

pygame.display.set_caption("Code Breaker — Hacker Simulator")

FONT = pygame.font.SysFont("consolas", 24)
FONT_SMALL = pygame.font.SysFont("consolas", 18)
FONT_TINY = pygame.font.SysFont("consolas", 15)
FONT_BIG = pygame.font.SysFont("consolas", 54)
FONT_TITLE = pygame.font.SysFont("consolas", 78, bold=True)

CLOCK = pygame.time.Clock()


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return os.getcwd()


APP_DIR = get_app_dir()
SAVE_PATH = os.path.join(APP_DIR, SAVE_FILE)


def default_save():
    return {
        "best_score": 0,
        "completed_missions": 0,
        "total_hacks": 0,
        "player_name": ""
    }


def load_save():
    data = default_save()

    if not os.path.exists(SAVE_PATH):
        return data

    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as file:
            loaded = json.load(file)

        if isinstance(loaded, dict):
            for key in data:
                if key in loaded:
                    data[key] = loaded[key]

    except Exception:
        return data

    try:
        data["best_score"] = int(data.get("best_score", 0))
        data["completed_missions"] = int(data.get("completed_missions", 0))
        data["total_hacks"] = int(data.get("total_hacks", 0))
        data["player_name"] = str(data.get("player_name", ""))[:18]
    except Exception:
        data = default_save()

    return data


def save_data(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception:
        pass


DATA = load_save()


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def draw_text(surface, text, x, y, font=FONT, color=WHITE, center=False, right=False):
    text = str(text)
    img = font.render(text, True, color)
    rect = img.get_rect()

    if center:
        rect.center = (int(x), int(y))
    elif right:
        rect.topright = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))

    surface.blit(img, rect)
    return rect


def draw_shadow_text(surface, text, x, y, font=FONT, color=WHITE, center=False):
    draw_text(surface, text, x + 2, y + 2, font, (0, 0, 0), center=center)
    return draw_text(surface, text, x, y, font, color, center=center)


def cut_text_to_width(text, font, max_width):
    text = str(text)
    max_width = max(20, int(max_width))

    if font.size(text)[0] <= max_width:
        return text

    dots = "..."
    result = ""

    for char in text:
        if font.size(result + char + dots)[0] <= max_width:
            result += char
        else:
            break

    return result + dots


def split_long_word(word, font, max_width):
    parts = []
    current = ""

    for char in str(word):
        if font.size(current + char)[0] <= max_width:
            current += char
        else:
            if current:
                parts.append(current)
            current = char

    if current:
        parts.append(current)

    return parts


def split_text_to_lines(text, font, max_width):
    text = str(text)
    max_width = max(50, int(max_width))
    lines = []

    for raw_line in text.split("\n"):
        words = raw_line.split(" ")
        current = ""

        for word in words:
            if word == "":
                continue

            if font.size(word)[0] > max_width:
                if current:
                    lines.append(current)
                    current = ""
                lines.extend(split_long_word(word, font, max_width))
                continue

            test_line = current + (" " if current else "") + word

            if font.size(test_line)[0] <= max_width:
                current = test_line
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

    return lines


def draw_text_clamped(surface, text, x, y, font=FONT, color=WHITE, max_width=300):
    fitted = cut_text_to_width(text, font, max_width)
    return draw_text(surface, fitted, x, y, font, color)


def draw_wrapped_text(surface, text, x, y, font=FONT_SMALL, color=WHITE,
                      max_width=400, line_height=24, max_lines=None):
    lines = split_text_to_lines(text, font, max_width)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = cut_text_to_width(lines[-1] + "...", font, max_width)

    current_y = y

    for line in lines:
        draw_text(surface, line, x, current_y, font, color)
        current_y += line_height

    return current_y


def draw_panel(surface, rect, color=PANEL, border=GREEN_DARK, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 2, border_radius=radius)

    # мягкая верхняя линия, чтобы панели выглядели объёмнее
    inner = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, max(12, rect.h // 5))
    pygame.draw.rect(surface, (24, 52, 64), inner, border_radius=radius)


def draw_progress_bar(surface, rect, value, max_value, fill_color=GREEN, back_color=DARK):
    value = clamp(value, 0, max_value)
    ratio = 0 if max_value <= 0 else value / max_value

    pygame.draw.rect(surface, back_color, rect, border_radius=6)
    fill_rect = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)

    if fill_rect.w > 0:
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=6)

    pygame.draw.rect(surface, GREEN_DARK, rect, 2, border_radius=6)


def draw_scanlines(surface):
    for y in range(0, BASE_HEIGHT, 4):
        pygame.draw.line(surface, (0, 0, 0), (0, y), (BASE_WIDTH, y), 1)


def draw_vignette(surface):
    overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 70), (0, 0, BASE_WIDTH, 40))
    pygame.draw.rect(overlay, (0, 0, 0, 70), (0, BASE_HEIGHT - 40, BASE_WIDTH, 40))
    pygame.draw.rect(overlay, (0, 0, 0, 55), (0, 0, 35, BASE_HEIGHT))
    pygame.draw.rect(overlay, (0, 0, 0, 55), (BASE_WIDTH - 35, 0, 35, BASE_HEIGHT))
    surface.blit(overlay, (0, 0))


def draw_glitch_text(surface, text, x, y, font, color, center=False):
    offset = random.choice([-2, -1, 0, 1, 2])
    draw_text(surface, text, x + offset, y, font, RED, center=center)
    draw_text(surface, text, x - offset, y + 1, font, CYAN, center=center)
    draw_text(surface, text, x, y, font, color, center=center)


def random_code(length):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


class Button:
    def __init__(self, x, y, w, h, text, action=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action

    def draw(self, surface, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        color = PANEL_HOVER if hover else (13, 32, 42)
        border = CYAN if hover else GREEN_DARK

        pygame.draw.rect(surface, color, self.rect, border_radius=9)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=9)

        if hover:
            glow_rect = self.rect.inflate(8, 8)
            pygame.draw.rect(surface, (0, 100, 120), glow_rect, 1, border_radius=11)

        fitted_text = cut_text_to_width(self.text, FONT, self.rect.width - 24)
        draw_text(
            surface,
            fitted_text,
            self.rect.centerx,
            self.rect.centery,
            FONT,
            WHITE if hover else GREEN,
            center=True
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()


class MatrixBackground:
    def __init__(self):
        self.columns = []
        self.create_columns()

    def create_columns(self):
        self.columns = []

        for x in range(0, BASE_WIDTH + 80, 18):
            self.columns.append({
                "x": x,
                "y": random.randint(-BASE_HEIGHT, BASE_HEIGHT),
                "speed": random.randint(2, 7),
                "chars": [random.choice("01ABCDEF#$%&") for _ in range(42)]
            })

    def update(self):
        for column in self.columns:
            column["y"] += column["speed"]

            if column["y"] > BASE_HEIGHT:
                column["y"] = random.randint(-540, -30)
                column["speed"] = random.randint(2, 7)
                column["chars"] = [random.choice("01ABCDEF#$%&") for _ in range(42)]

    def draw(self, surface):
        for column in self.columns:
            x = column["x"]
            y = column["y"]

            for i, char in enumerate(column["chars"]):
                draw_y = y + i * 20

                if -30 <= draw_y <= BASE_HEIGHT + 30:
                    value = max(35, 185 - i * 5)
                    color = (0, value, 92)
                    draw_text(surface, char, x, draw_y, FONT_SMALL, color)


class Scene:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass


class NameScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.name_input = DATA.get("player_name", "")
        self.message = "Введите имя игрока"
        self.start_button = Button(430, 445, 340, 56, "ПРОДОЛЖИТЬ", self.continue_game)

    def continue_game(self):
        name = self.name_input.strip()

        if len(name) < 2:
            self.message = "Имя должно быть минимум 2 символа"
            return

        DATA["player_name"] = name[:18]
        save_data(DATA)
        self.app.change_scene(MenuScene(self.app))

    def handle_event(self, event):
        self.start_button.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.continue_game()
            elif event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif event.key == pygame.K_ESCAPE:
                if DATA.get("player_name", "").strip() != "":
                    self.app.change_scene(MenuScene(self.app))
            else:
                if len(self.name_input) < 18:
                    char = event.unicode
                    if char.isalnum() or char in " _-":
                        self.name_input += char

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        draw_glitch_text(surface, "CODE BREAKER", BASE_WIDTH // 2, 82, FONT_TITLE, GREEN, center=True)
        draw_text(surface, "РЕГИСТРАЦИЯ ИГРОКА", BASE_WIDTH // 2, 180, FONT, CYAN, center=True)

        panel = pygame.Rect(330, 240, 540, 290)
        draw_panel(surface, panel)

        draw_text(surface, self.message, BASE_WIDTH // 2, 275, FONT, YELLOW, center=True)

        input_rect = pygame.Rect(400, 340, 400, 60)
        pygame.draw.rect(surface, DARK, input_rect, border_radius=8)
        pygame.draw.rect(surface, CYAN, input_rect, 2, border_radius=8)

        shown_name = self.name_input
        if int(time.time() * 2) % 2 == 0:
            shown_name += "_"
        if shown_name.strip() == "_":
            shown_name = "_"

        draw_text_clamped(surface, shown_name, 420, 354, FONT, GREEN, 360)
        self.start_button.draw(surface, self.app.mouse_pos)

        draw_text(surface, "Enter — продолжить", 420, 555, FONT_SMALL, GRAY)
        draw_text(surface, "F11 — полный экран / оконный режим", 420, 580, FONT_SMALL, GRAY)
        draw_scanlines(surface)


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [
            Button(430, 285, 340, 56, "НАЧАТЬ МИССИЮ", self.start_game),
            Button(430, 355, 340, 56, "ОБУЧЕНИЕ", self.training),
            Button(430, 425, 340, 56, "СТАТИСТИКА", self.stats),
            Button(430, 495, 340, 56, "ВЫХОД", self.exit_game),
        ]

    def start_game(self):
        self.app.change_scene(GameScene(self.app))

    def training(self):
        self.app.change_scene(TrainingScene(self.app))

    def stats(self):
        self.app.change_scene(StatsScene(self.app))

    def exit_game(self):
        save_data(DATA)
        pygame.quit()
        sys.exit()

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.exit_game()

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        draw_glitch_text(surface, "CODE BREAKER", BASE_WIDTH // 2, 92, FONT_TITLE, GREEN, center=True)
        draw_text(surface, "HACKER SIMULATOR", BASE_WIDTH // 2, 185, FONT, CYAN, center=True)

        draw_panel(surface, pygame.Rect(370, 245, 460, 330))

        for button in self.buttons:
            button.draw(surface, self.app.mouse_pos)

        player_name = DATA.get("player_name", "STUDENT")
        draw_text_clamped(surface, f"Игрок: {player_name}", 20, 20, FONT_SMALL, GRAY, 430)
        draw_text(surface, "ESC — выход из игры", 20, BASE_HEIGHT - 35, FONT_SMALL, GRAY)
        draw_text(surface, "F11 — полный экран", BASE_WIDTH - 230, BASE_HEIGHT - 35, FONT_SMALL, GRAY)
        draw_scanlines(surface)


class TrainingScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.back_button = Button(40, 620, 240, 50, "НАЗАД В МЕНЮ", self.back)

    def back(self):
        self.app.change_scene(MenuScene(self.app))

    def handle_event(self, event):
        self.back_button.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        draw_text(surface, "ОБУЧЕНИЕ", BASE_WIDTH // 2, 55, FONT_BIG, GREEN, center=True)

        panel_rect = pygame.Rect(90, 120, 1020, 430)
        draw_panel(surface, panel_rect)

        lines = [
            "Ты играешь за начинающего специалиста по кибербезопасности.",
            "Твоя задача — взламывать тренировочные цифровые коды.",
            "",
            "Правила:",
            "1. Система генерирует секретный цифровой код.",
            "2. Игрок вводит набор цифр.",
            "3. После каждой попытки отображается анализ результата.",
            "4. Точное совпадение означает, что цифра и позиция верны.",
            "5. Если цифра есть в коде, но позиция другая, система тоже сообщает об этом.",
            "6. После пяти неправильных попыток система выдаёт подсказку.",
            "",
            "Управление:",
            "Цифры 0–9 — ввод кода. Backspace — удалить символ. Enter — отправить попытку.",
            "ESC — вернуться в меню. F11 — полный экран."
        ]

        y = 145
        for line in lines:
            if line == "":
                y += 10
                continue

            color = CYAN if line.endswith(":") else WHITE
            y = draw_wrapped_text(surface, line, 120, y, FONT_SMALL, color, max_width=930, line_height=23)
            y += 1

        self.back_button.draw(surface, self.app.mouse_pos)
        draw_scanlines(surface)


class StatsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.back_button = Button(40, 620, 240, 50, "НАЗАД В МЕНЮ", self.back)
        self.reset_button = Button(920, 620, 220, 50, "СБРОСИТЬ", self.reset)
        self.name_button = Button(455, 540, 290, 50, "СМЕНИТЬ ИМЯ", self.change_name)
        self.info_message = ""

    def back(self):
        self.app.change_scene(MenuScene(self.app))

    def reset(self):
        DATA["best_score"] = 0
        DATA["completed_missions"] = 0
        DATA["total_hacks"] = 0
        save_data(DATA)
        self.info_message = "Статистика сброшена"

    def change_name(self):
        self.app.change_scene(NameScene(self.app))

    def handle_event(self, event):
        self.back_button.handle_event(event)
        self.reset_button.handle_event(event)
        self.name_button.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        draw_text(surface, "СТАТИСТИКА", BASE_WIDTH // 2, 65, FONT_BIG, GREEN, center=True)

        panel_rect = pygame.Rect(300, 145, 600, 380)
        draw_panel(surface, panel_rect)

        draw_text(surface, "ДАННЫЕ ПРОФИЛЯ", 360, 185, FONT, CYAN)
        draw_text_clamped(surface, f"Игрок: {DATA.get('player_name', 'STUDENT')}", 360, 235, FONT, WHITE, 480)
        draw_text_clamped(surface, f"Лучший результат: {DATA['best_score']}", 360, 285, FONT, WHITE, 480)
        draw_text_clamped(surface, f"Пройдено миссий: {DATA['completed_missions']}", 360, 335, FONT, WHITE, 480)
        draw_text_clamped(surface, f"Всего успешных взломов: {DATA['total_hacks']}", 360, 385, FONT, WHITE, 480)

        draw_wrapped_text(
            surface,
            "Статистика сохраняется автоматически в файл save_data.json рядом с игрой.",
            360,
            445,
            FONT_SMALL,
            GRAY,
            max_width=500,
            line_height=21,
            max_lines=3
        )

        if self.info_message:
            draw_text(surface, self.info_message, BASE_WIDTH // 2, 505, FONT_SMALL, YELLOW, center=True)

        self.name_button.draw(surface, self.app.mouse_pos)
        self.back_button.draw(surface, self.app.mouse_pos)
        self.reset_button.draw(surface, self.app.mouse_pos)
        draw_scanlines(surface)


class GameScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.level = 1
        self.score = 0
        self.input_text = ""
        self.log = []
        self.message = "СИСТЕМА ОЖИДАЕТ ВВОД..."
        self.menu_button = Button(920, 35, 220, 48, "В МЕНЮ", self.go_menu)

        self.missions = [
            "Учебный сервер колледжа",
            "Локальная сеть лаборатории",
            "Архив цифровых пропусков",
            "Тестовый банковский шлюз",
            "Симулятор корпоративной защиты",
            "Закрытый тренировочный контур"
        ]

        self.wrong_attempts = 0
        self.hint_given = False
        self.hint_text = "Подсказка появится после 5 ошибок."
        self.start_level()

    def go_menu(self):
        pygame.time.set_timer(NEXT_LEVEL_EVENT, 0)
        self.app.change_scene(MenuScene(self.app))

    def start_level(self):
        self.code_length = min(4 + self.level // 2, 7)
        self.secret = random_code(self.code_length)
        self.attempts_max = max(12 - self.level, 5)
        self.attempts_left = self.attempts_max
        self.time_limit = max(90 - self.level * 5, 35)
        self.start_time = time.time()
        self.input_text = ""
        self.log = []
        self.mission_name = self.missions[(self.level - 1) % len(self.missions)]
        self.message = f"МИССИЯ {self.level}: подобрать {self.code_length}-значный код"
        self.wrong_attempts = 0
        self.hint_given = False
        self.hint_text = "Подсказка появится после 5 ошибок."

    def make_hint(self):
        if self.hint_given:
            return

        index = random.randint(0, len(self.secret) - 1)
        digit = self.secret[index]
        self.hint_text = f"Подсказка: цифра №{index + 1} равна {digit}"
        self.hint_given = True

    def check_guess(self, guess):
        exact = 0
        exists = 0
        secret_list = list(self.secret)
        guess_list = list(guess)

        for i in range(len(guess_list)):
            if guess_list[i] == secret_list[i]:
                exact += 1
                secret_list[i] = None
                guess_list[i] = None

        for i in range(len(guess_list)):
            if guess_list[i] is not None and guess_list[i] in secret_list:
                exists += 1
                secret_list[secret_list.index(guess_list[i])] = None

        return exact, exists

    def submit(self):
        if len(self.input_text) != self.code_length:
            self.message = f"Нужно ввести {self.code_length} цифр"
            return

        exact, exists = self.check_guess(self.input_text)
        self.log.insert(0, {
            "guess": self.input_text,
            "exact": exact,
            "exists": exists
        })

        if len(self.log) > 8:
            self.log = self.log[:8]

        if exact == self.code_length:
            gained = self.attempts_left * 100 + int(self.get_time_left()) * 5 + self.level * 250
            self.score += gained
            DATA["completed_missions"] += 1
            DATA["total_hacks"] += 1

            if self.score > DATA["best_score"]:
                DATA["best_score"] = self.score

            save_data(DATA)
            self.message = f"КОД ВЗЛОМАН! +{gained} очков. Переход дальше..."
            self.input_text = ""
            self.level += 1
            pygame.time.set_timer(NEXT_LEVEL_EVENT, 1200, loops=1)
            return

        self.attempts_left -= 1
        self.wrong_attempts += 1

        if self.wrong_attempts >= 5 and not self.hint_given:
            self.make_hint()
            self.message = f"ТОЧНО: {exact} | ЕСТЬ: {exists} | ПОДСКАЗКА ОТКРЫТА"
        else:
            self.message = f"ТОЧНО: {exact} | ЕСТЬ В КОДЕ: {exists}"

        self.input_text = ""

        if self.attempts_left <= 0:
            self.app.change_scene(ResultScene(self.app, False, self.score, self.secret))

    def get_time_left(self):
        passed = time.time() - self.start_time
        return max(0, self.time_limit - passed)

    def handle_event(self, event):
        self.menu_button.handle_event(event)

        if event.type == NEXT_LEVEL_EVENT:
            self.start_level()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.go_menu()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_RETURN:
                self.submit()
            elif event.unicode.isdigit():
                if len(self.input_text) < self.code_length:
                    self.input_text += event.unicode

    def update(self):
        if self.get_time_left() <= 0:
            self.app.change_scene(ResultScene(self.app, False, self.score, self.secret))

    def draw_terminal(self, surface):
        terminal_rect = pygame.Rect(40, 120, 720, 520)
        draw_panel(surface, terminal_rect)

        draw_text(surface, "ТЕРМИНАЛ ВЗЛОМА", 65, 145, FONT, GREEN)
        draw_text_clamped(surface, f"Цель: {self.mission_name}", 65, 185, FONT_SMALL, GRAY, 650)
        draw_text_clamped(surface, f"Уровень доступа: {self.level}", 65, 210, FONT_SMALL, GRAY, 650)

        pygame.draw.line(surface, GREEN_DARK, (65, 245), (735, 245), 2)
        draw_text(surface, "Введите код:", 65, 275, FONT, WHITE)

        input_rect = pygame.Rect(65, 315, 420, 60)
        pygame.draw.rect(surface, DARK, input_rect, border_radius=8)
        pygame.draw.rect(surface, CYAN, input_rect, 2, border_radius=8)

        shown = self.input_text + "_" * (self.code_length - len(self.input_text))
        draw_text_clamped(surface, shown, 85, 330, FONT_BIG, GREEN, 380)

        draw_wrapped_text(
            surface,
            self.message,
            65,
            400,
            FONT_SMALL,
            YELLOW,
            max_width=650,
            line_height=22,
            max_lines=2
        )

        draw_text(surface, "История попыток:", 65, 455, FONT, CYAN)
        y = 490

        for item in self.log[:5]:
            text = f"{item['guess']} | точные: {item['exact']} | есть: {item['exists']}"
            draw_text_clamped(surface, text, 65, y, FONT_SMALL, WHITE, 650)
            y += 27

    def draw_hud(self, surface):
        hud_rect = pygame.Rect(800, 120, 350, 500)
        draw_panel(surface, hud_rect)

        draw_text(surface, "ПАНЕЛЬ ИГОРКА", 825, 145, FONT, GREEN)
        time_left = int(self.get_time_left())

        draw_text_clamped(surface, f"Время: {time_left} сек", 825, 190, FONT_SMALL, WHITE, 290)
        draw_progress_bar(surface, pygame.Rect(825, 213, 300, 13), time_left, self.time_limit, GREEN if time_left > 15 else RED)

        draw_text_clamped(surface, f"Попытки: {self.attempts_left}/{self.attempts_max}", 825, 240, FONT_SMALL, WHITE, 290)
        draw_progress_bar(surface, pygame.Rect(825, 263, 300, 13), self.attempts_left, self.attempts_max, CYAN)

        draw_text_clamped(surface, f"Ошибки: {self.wrong_attempts}/5", 825, 290, FONT_SMALL, WHITE, 290)
        draw_text_clamped(surface, f"Длина кода: {self.code_length}", 825, 318, FONT_SMALL, WHITE, 290)
        draw_text_clamped(surface, f"Счёт: {self.score}", 825, 346, FONT_SMALL, WHITE, 290)

        pygame.draw.line(surface, GREEN_DARK, (825, 380), (1125, 380), 2)
        draw_text(surface, "Подсказка:", 825, 400, FONT_SMALL, CYAN)

        draw_wrapped_text(
            surface,
            self.hint_text,
            825,
            427,
            FONT_TINY,
            YELLOW if self.hint_given else GRAY,
            max_width=285,
            line_height=18,
            max_lines=3
        )

        pygame.draw.line(surface, GREEN_DARK, (825, 495), (1125, 495), 2)
        draw_text(surface, "Управление:", 825, 513, FONT_SMALL, CYAN)
        draw_text(surface, "Enter — проверить", 825, 540, FONT_TINY, GRAY)
        draw_text(surface, "Backspace — удалить", 825, 560, FONT_TINY, GRAY)
        draw_text(surface, "ESC — выйти в меню", 825, 580, FONT_TINY, YELLOW)
        draw_text(surface, "F11 — полный экран", 825, 600, FONT_TINY, CYAN)

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        draw_text(surface, "CODE BREAKER", 40, 35, FONT_BIG, GREEN)
        draw_text_clamped(surface, "режим: тренировочный симулятор кибербезопасности", 45, 88, FONT_SMALL, CYAN, 650)

        player_name = DATA.get("player_name", "STUDENT")
        draw_text_clamped(surface, f"Игрок: {player_name}", 560, 45, FONT_SMALL, GRAY, 330)
        self.menu_button.draw(surface, self.app.mouse_pos)

        self.draw_terminal(surface)
        self.draw_hud(surface)
        draw_scanlines(surface)


class ResultScene(Scene):
    def __init__(self, app, win, score, secret):
        super().__init__(app)
        self.win = win
        self.score = score
        self.secret = secret
        self.buttons = [
            Button(430, 390, 340, 56, "В МЕНЮ", self.menu),
            Button(430, 465, 340, 56, "НОВАЯ ИГРА", self.restart),
        ]

    def menu(self):
        self.app.change_scene(MenuScene(self.app))

    def restart(self):
        self.app.change_scene(GameScene(self.app))

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.menu()

    def draw(self, surface):
        surface.fill(BLACK)
        self.app.bg.draw(surface)
        draw_vignette(surface)

        title = "МИССИЯ ПРОВАЛЕНА" if not self.win else "МИССИЯ ВЫПОЛНЕНА"
        color = RED if not self.win else GREEN
        draw_text(surface, title, BASE_WIDTH // 2, 150, FONT_BIG, color, center=True)

        panel = pygame.Rect(320, 235, 560, 125)
        draw_panel(surface, panel)
        draw_text_clamped(surface, f"Финальный счёт: {self.score}", 375, 265, FONT, WHITE, 450)
        draw_text_clamped(surface, f"Секретный код был: {self.secret}", 375, 310, FONT, YELLOW, 450)

        for button in self.buttons:
            button.draw(surface, self.app.mouse_pos)

        draw_text(surface, "ESC — назад в меню", BASE_WIDTH // 2, 555, FONT_SMALL, GRAY, center=True)
        draw_scanlines(surface)


class CodeBreakerApp:
    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode(WINDOWED_SIZE, pygame.RESIZABLE)
        self.canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)).convert()
        self.scale = 1.0
        self.offset = (0, 0)
        self.scaled_size = WINDOWED_SIZE
        self.mouse_pos = (0, 0)
        self.bg = MatrixBackground()
        self.update_render_layout()

        if DATA.get("player_name", "").strip() == "":
            self.scene = NameScene(self)
        else:
            self.scene = MenuScene(self)

    def update_render_layout(self):
        screen_w, screen_h = self.screen.get_size()
        scale_x = screen_w / BASE_WIDTH
        scale_y = screen_h / BASE_HEIGHT
        self.scale = min(scale_x, scale_y)

        if self.scale <= 0:
            self.scale = 1.0

        scaled_w = max(1, int(BASE_WIDTH * self.scale))
        scaled_h = max(1, int(BASE_HEIGHT * self.scale))
        self.scaled_size = (scaled_w, scaled_h)
        self.offset = ((screen_w - scaled_w) // 2, (screen_h - scaled_h) // 2)

    def screen_to_virtual(self, pos):
        x, y = pos
        ox, oy = self.offset
        vx = (x - ox) / self.scale
        vy = (y - oy) / self.scale

        if vx < 0 or vy < 0 or vx > BASE_WIDTH or vy > BASE_HEIGHT:
            return (-10000, -10000)

        return (int(vx), int(vy))

    def convert_mouse_event(self, event):
        if hasattr(event, "pos"):
            data = event.__dict__.copy()
            data["pos"] = self.screen_to_virtual(event.pos)
            return pygame.event.Event(event.type, data)
        return event

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            self.screen = pygame.display.set_mode(WINDOWED_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF)

        pygame.display.set_caption("Code Breaker — Hacker Simulator")
        self.update_render_layout()

    def change_scene(self, scene):
        self.scene = scene

    def handle_resize(self, event):
        if self.fullscreen:
            return

        new_w = max(MIN_WINDOW_SIZE[0], event.w)
        new_h = max(MIN_WINDOW_SIZE[1], event.h)
        self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.update_render_layout()

    def render(self):
        self.scene.draw(self.canvas)

        if self.scaled_size == (BASE_WIDTH, BASE_HEIGHT):
            frame = self.canvas
        else:
            frame = pygame.transform.smoothscale(self.canvas, self.scaled_size)

        self.screen.fill(BLACK)
        self.screen.blit(frame, self.offset)
        pygame.display.flip()

    def run(self):
        while True:
            CLOCK.tick(FPS)
            self.mouse_pos = self.screen_to_virtual(pygame.mouse.get_pos())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_data(DATA)
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event)
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue

                event = self.convert_mouse_event(event)
                self.scene.handle_event(event)

            self.bg.update()
            self.scene.update()
            self.render()


if __name__ == "__main__":
    app = CodeBreakerApp()
    app.run()
