#!/usr/bin/env python3
"""
贪吃蛇 - Terminal Snake Game
操作: WASD 或方向键移动, Q 退出, P 暂停
"""

import curses
import random
import time

# 方向常量
UP    = (-1, 0)
DOWN  = ( 1, 0)
LEFT  = ( 0,-1)
RIGHT = ( 0, 1)

OPPOSITES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

KEY_MAP = {
    curses.KEY_UP:    UP,    ord('w'): UP,    ord('W'): UP,
    curses.KEY_DOWN:  DOWN,  ord('s'): DOWN,  ord('S'): DOWN,
    curses.KEY_LEFT:  LEFT,  ord('a'): LEFT,  ord('A'): LEFT,
    curses.KEY_RIGHT: RIGHT, ord('d'): RIGHT, ord('D'): RIGHT,
}

LEVELS = [
    {"name": "简单", "speed": 0.18, "walls": False},
    {"name": "普通", "speed": 0.12, "walls": True},
    {"name": "困难", "speed": 0.07, "walls": True},
]

def draw_border(win, h, w, color):
    win.attron(color)
    win.border('│', '│', '─', '─', '╔', '╗', '╚', '╝')
    win.attroff(color)

def place_food(snake_set, h, w, walls):
    while True:
        r = random.randint(1, h - 2)
        c = random.randint(1, w - 2)
        if (r, c) not in snake_set:
            return (r, c)

def show_menu(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title_lines = [
        "╔══════════════════════╗",
        "║    🐍  贪吃蛇游戏     ║",
        "╚══════════════════════╝",
    ]
    ascii_snake = [
        "  ____   ____  ",
        " / ___| |  _ \\ ",
        " \\___ \\ | | | |",
        "  ___) || |_| |",
        " |____/ |____/ ",
    ]

    # Colors
    curses.init_pair(1, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    selected = 0
    while True:
        stdscr.clear()
        # Title
        start_r = max(1, h // 2 - 10)
        for i, line in enumerate(title_lines):
            c = max(0, w // 2 - len(line) // 2)
            try:
                stdscr.addstr(start_r + i, c, line, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

        # Instructions
        instructions = [
            ("", 0),
            ("  选择难度  ", 2),
            ("", 0),
        ]
        for i, (lvl) in enumerate(LEVELS):
            marker = "▶ " if i == selected else "  "
            attr = curses.color_pair(2) | curses.A_BOLD if i == selected else curses.color_pair(4)
            label = f"{marker}{lvl['name']}  速度:{int(1/lvl['speed'])}  {'有墙壁' if lvl['walls'] else '无墙壁'}"
            instructions.append((label, attr if i == selected else 4))

        instructions += [
            ("", 0),
            ("  [↑↓] 选择   [Enter] 开始   [Q] 退出  ", 5),
            ("", 0),
            ("  操作: WASD 或方向键  P=暂停  Q=退出  ", 4),
        ]

        for j, (text, color_idx) in enumerate(instructions):
            r = start_r + len(title_lines) + j
            c = max(0, w // 2 - len(text) // 2)
            try:
                if color_idx == 0:
                    pass
                elif color_idx == 5:
                    stdscr.addstr(r, c, text, curses.color_pair(5) | curses.A_BOLD)
                else:
                    attr = curses.color_pair(color_idx) | curses.A_BOLD if color_idx == 2 else curses.color_pair(color_idx)
                    stdscr.addstr(r, c, text, attr)
            except curses.error:
                pass

        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('w'), ord('W')):
            selected = (selected - 1) % len(LEVELS)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S')):
            selected = (selected + 1) % len(LEVELS)
        elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER):
            return selected
        elif key in (ord('q'), ord('Q')):
            return None

def game_over_screen(stdscr, score, high_score, won=False):
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    msg = "你赢了！！！ 🎉" if won else "游戏结束！"
    lines = [
        msg,
        f"得分: {score}",
        f"最高分: {high_score}",
        "",
        "[R] 重试   [M] 菜单   [Q] 退出",
    ]
    start_r = h // 2 - len(lines) // 2
    for i, line in enumerate(lines):
        c = max(0, w // 2 - len(line) // 2)
        color = curses.color_pair(1) if won else curses.color_pair(3)
        try:
            stdscr.addstr(start_r + i, c, line, color | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord('r'), ord('R')):
            return 'retry'
        elif key in (ord('m'), ord('M')):
            return 'menu'
        elif key in (ord('q'), ord('Q')):
            return 'quit'

def play(stdscr, level_idx, high_score):
    level = LEVELS[level_idx]
    speed = level["speed"]
    walls = level["walls"]

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(int(speed * 1000))
    h, w = stdscr.getmaxyx()

    # Color pairs
    curses.init_pair(1, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_WHITE,   curses.COLOR_BLACK)

    # Init snake in center
    mid_r, mid_c = h // 2, w // 2
    snake = [(mid_r, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c - 2)]
    snake_set = set(snake)
    direction = RIGHT
    next_dir = RIGHT

    food = place_food(snake_set, h, w, walls)
    score = 0
    paused = False

    # Special food (bonus)
    bonus_food = None
    bonus_timer = 0
    bonus_interval = 10  # every 10 points a bonus appears

    while True:
        key = stdscr.getch()

        if key == ord('q') or key == ord('Q'):
            return 'quit', score
        elif key == ord('p') or key == ord('P'):
            paused = not paused
            if paused:
                stdscr.nodelay(False)
            else:
                stdscr.nodelay(True)
                stdscr.timeout(int(speed * 1000))
        elif key in KEY_MAP:
            nd = KEY_MAP[key]
            if nd != OPPOSITES.get(direction):
                next_dir = nd

        if paused:
            # Show pause overlay
            msg = "  ⏸  已暂停 — 按 P 继续  "
            try:
                stdscr.addstr(h // 2, max(0, w // 2 - len(msg) // 2), msg,
                              curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.refresh()
            continue

        direction = next_dir
        head = snake[0]
        new_head = (head[0] + direction[0], head[1] + direction[1])

        # Wall collision
        if walls:
            if new_head[0] <= 0 or new_head[0] >= h - 1 or new_head[1] <= 0 or new_head[1] >= w - 1:
                return 'dead', score
        else:
            # Wrap around
            new_head = (new_head[0] % h, new_head[1] % w)

        # Self collision
        if new_head in snake_set:
            return 'dead', score

        # Eat food
        ate = False
        bonus_pts = 0
        if new_head == food:
            ate = True
            score += 1
            food = place_food(snake_set | {new_head}, h, w, walls)
            # Spawn bonus every bonus_interval points
            if score % bonus_interval == 0:
                bonus_food = place_food(snake_set | {new_head, food}, h, w, walls)
                bonus_timer = 15  # disappears after 15 moves

        if bonus_food and new_head == bonus_food:
            bonus_pts = 5
            score += bonus_pts
            bonus_food = None
            bonus_timer = 0

        snake.insert(0, new_head)
        snake_set.add(new_head)
        if not ate:
            tail = snake.pop()
            snake_set.discard(tail)

        # Bonus timer countdown
        if bonus_food:
            bonus_timer -= 1
            if bonus_timer <= 0:
                bonus_food = None

        # Win condition: snake fills ~70% of playable area
        playable = (h - 2) * (w - 2)
        if len(snake) >= int(playable * 0.7):
            return 'won', score

        # Draw
        stdscr.clear()

        # Border
        border_color = curses.color_pair(1) if not walls else curses.color_pair(3)
        draw_border(stdscr, h, w, border_color)

        # Snake body
        for i, (r, c) in enumerate(snake):
            if 0 <= r < h and 0 <= c < w:
                if i == 0:
                    try:
                        stdscr.addstr(r, c, '◉', curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    shade = curses.color_pair(1) if i % 2 == 0 else curses.color_pair(4)
                    try:
                        stdscr.addstr(r, c, '●', shade)
                    except curses.error:
                        pass

        # Food
        fr, fc = food
        try:
            stdscr.addstr(fr, fc, '◆', curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # Bonus food
        if bonus_food:
            br, bc = bonus_food
            blink = curses.A_BOLD | (curses.A_BLINK if bonus_timer < 6 else 0)
            try:
                stdscr.addstr(br, bc, '★', curses.color_pair(2) | blink)
            except curses.error:
                pass

        # HUD
        hud = f" 得分:{score}  最高:{high_score}  难度:{level['name']}  长度:{len(snake)}  P=暂停 "
        try:
            stdscr.addstr(0, max(0, w // 2 - len(hud) // 2), hud, curses.color_pair(6))
        except curses.error:
            pass

        stdscr.refresh()

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    high_score = 0

    while True:
        level_idx = show_menu(stdscr)
        if level_idx is None:
            break

        while True:
            result, score = play(stdscr, level_idx, high_score)
            high_score = max(high_score, score)

            if result == 'quit':
                return
            elif result in ('dead', 'won'):
                action = game_over_screen(stdscr, score, high_score, won=(result == 'won'))
                if action == 'retry':
                    continue
                elif action == 'menu':
                    break
                else:
                    return

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("感谢游玩！再见 👋")
