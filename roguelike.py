#!/usr/bin/env python3
"""
地牢探险 Roguelike - A terminal dungeon crawler
Controls: WASD/Arrow keys=move, G=pickup, I=inventory, U=use item, >/<= stairs, Q=quit
"""

import curses
import random
import math
from collections import deque

# ─────────────────────────── Constants ───────────────────────────

MAP_W, MAP_H = 80, 40
MAX_ROOMS     = 18
MIN_ROOM_SIZE = 4
MAX_ROOM_SIZE = 10
FOV_RADIUS    = 8
MAX_DEPTH     = 6   # floors

COLORS = {}  # populated in init_colors()

# ─────────────────────────── Data Classes ────────────────────────

class Rect:
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w, y + h

    def center(self):
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Tile:
    __slots__ = ['walkable', 'transparent', 'glyph', 'color', 'explored']
    def __init__(self, walkable, transparent, glyph, color):
        self.walkable    = walkable
        self.transparent = transparent
        self.glyph       = glyph
        self.color       = color
        self.explored    = False


class Entity:
    def __init__(self, x, y, glyph, color, name):
        self.x, self.y = x, y
        self.glyph     = glyph
        self.color     = color
        self.name      = name


class Fighter:
    def __init__(self, hp, defense, power, xp_value=0):
        self.max_hp    = hp
        self.hp        = hp
        self.defense   = defense
        self.power     = power
        self.xp_value  = xp_value


class Item:
    def __init__(self, kind, value, name, glyph='!', color='yellow'):
        self.kind  = kind    # 'potion_hp','potion_mp','weapon','armor','scroll'
        self.value = value
        self.name  = name
        self.glyph = glyph
        self.color = color


class Monster(Entity):
    AI_IDLE    = 'idle'
    AI_CHASE   = 'chase'
    AI_PATROL  = 'patrol'

    def __init__(self, x, y, glyph, color, name, fighter, ai=AI_IDLE):
        super().__init__(x, y, glyph, color, name)
        self.fighter = fighter
        self.ai_state = ai
        self.patrol_target = None
        self.alert_range = 6

    def is_alive(self):
        return self.fighter.hp > 0


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, '@', 'white_bold', '勇者')
        self.fighter = Fighter(hp=30, defense=2, power=5)
        self.level   = 1
        self.xp      = 0
        self.xp_next = 20
        self.mp      = 10
        self.max_mp  = 10
        self.gold    = 0
        self.inventory = []   # list of Item
        self.weapon    = None
        self.armor     = None
        self.max_inventory = 10
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.kills = 0
        self.deepest_floor = 1

    def level_up(self):
        self.level     += 1
        self.fighter.max_hp += 8
        self.fighter.hp      = self.fighter.max_hp
        self.fighter.power  += 2
        self.fighter.defense += 1
        self.xp_next  = int(self.xp_next * 1.6)
        return f"升级！达到 {self.level} 级！HP+8 ATK+2 DEF+1"

    @property
    def total_power(self):
        base = self.fighter.power + self.attack_bonus
        if self.weapon:
            base += self.weapon.value
        return base

    @property
    def total_defense(self):
        base = self.fighter.defense + self.defense_bonus
        if self.armor:
            base += self.armor.value
        return base


# ─────────────────────────── Map Generation ──────────────────────

def make_tile(kind):
    if kind == 'wall':
        return Tile(False, False, '#', 'wall')
    if kind == 'floor':
        return Tile(True, True, '.', 'floor')
    if kind == 'door':
        return Tile(True, False, '+', 'door')
    if kind == 'stair_down':
        return Tile(True, True, '>', 'stair')
    if kind == 'stair_up':
        return Tile(True, True, '<', 'stair')
    return Tile(False, False, ' ', 'wall')


def generate_map(depth):
    tiles = [[make_tile('wall') for _ in range(MAP_W)] for _ in range(MAP_H)]
    rooms = []
    monsters = []
    items = []

    n_rooms = random.randint(8, MAX_ROOMS)

    for _ in range(200):
        if len(rooms) >= n_rooms:
            break
        w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
        h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
        x = random.randint(1, MAP_W - w - 2)
        y = random.randint(1, MAP_H - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(r) for r in rooms):
            continue

        # Carve room
        for ry in range(new_room.y1, new_room.y2):
            for rx in range(new_room.x1, new_room.x2):
                tiles[ry][rx] = make_tile('floor')

        if rooms:
            # Connect to previous room
            prev_cx, prev_cy = rooms[-1].center()
            cx, cy = new_room.center()
            if random.random() < 0.5:
                carve_h_tunnel(tiles, prev_cx, cx, prev_cy)
                carve_v_tunnel(tiles, prev_cy, cy, cx)
            else:
                carve_v_tunnel(tiles, prev_cy, cy, prev_cx)
                carve_h_tunnel(tiles, prev_cx, cx, cy)

        rooms.append(new_room)

        # Populate (skip first room = player start)
        if len(rooms) > 1:
            _populate_room(new_room, depth, monsters, items, tiles)

    # Place stairs
    down_room = rooms[-1]
    cx, cy = down_room.center()
    tiles[cy][cx] = make_tile('stair_down')

    up_room = rooms[0]
    ucx, ucy = up_room.center()
    if depth > 1:
        tiles[ucy][ucx] = make_tile('stair_up')

    start_x, start_y = rooms[0].center()
    return tiles, rooms, monsters, items, start_x, start_y


def carve_h_tunnel(tiles, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 < y < MAP_H - 1 and 0 < x < MAP_W - 1:
            tiles[y][x] = make_tile('floor')


def carve_v_tunnel(tiles, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 < y < MAP_H - 1 and 0 < x < MAP_W - 1:
            tiles[y][x] = make_tile('floor')


MONSTER_TEMPLATES = [
    # (name, glyph, color, hp, def, pwr, xp, min_depth)
    ('老鼠',   'r', 'brown',   4,  0, 2,  2, 1),
    ('蝙蝠',   'b', 'yellow',  5,  0, 3,  3, 1),
    ('哥布林', 'g', 'green',   8,  1, 4,  5, 1),
    ('骷髅',   's', 'white',  10,  1, 5,  7, 2),
    ('兽人',   'O', 'green',  14,  2, 7, 10, 2),
    ('食人魔', 'T', 'red',    20,  3, 9, 15, 3),
    ('巫师',   'W', 'cyan',   12,  1, 8, 14, 3),
    ('龙人',   'D', 'magenta',25,  4,12, 22, 4),
    ('吸血鬼', 'V', 'red',    18,  3,10, 18, 4),
    ('巨龙',   'X', 'red_bold',40, 6,18, 50, 5),
]

ITEM_TEMPLATES = [
    # (name, kind, value, glyph, color, min_depth, weight)
    ('小血药',    'potion_hp', 10, '!', 'red',    1, 30),
    ('大血药',    'potion_hp', 25, '!', 'red',    2, 15),
    ('魔力药水',  'potion_mp',  8, '!', 'cyan',   1, 20),
    ('铁剑',      'weapon',     3, '/', 'white',  1, 20),
    ('钢剑',      'weapon',     6, '/', 'cyan',   2, 12),
    ('精灵弯刀',  'weapon',    10, '/', 'green',  3,  6),
    ('皮甲',      'armor',      2, '[', 'brown',  1, 20),
    ('锁甲',      'armor',      5, '[', 'white',  2, 12),
    ('魔法盾甲',  'armor',      9, '[', 'cyan',   4,  5),
    ('闪电卷轴',  'scroll',    15, '?', 'yellow', 2, 10),
    ('金币袋',    'gold',      random.randint(5,30), '$', 'yellow', 1, 25),
]


def _populate_room(room, depth, monsters, items, tiles):
    # Monsters
    n_monsters = random.randint(0, 2 + depth // 2)
    valid = [t for t in MONSTER_TEMPLATES if t[8] <= depth]
    if not valid:
        valid = MONSTER_TEMPLATES[:3]

    for _ in range(n_monsters):
        mx = random.randint(room.x1, room.x2 - 1)
        my = random.randint(room.y1, room.y2 - 1)
        if not tiles[my][mx].walkable:
            continue
        tpl = random.choices(valid, weights=[1]*len(valid))[0]
        scale = 1 + (depth - tpl[8]) * 0.15
        m = Monster(
            mx, my, tpl[1], tpl[2], tpl[0],
            Fighter(
                int(tpl[3] * scale),
                int(tpl[4] * scale),
                int(tpl[5] * scale),
                int(tpl[6] * scale)
            ),
            ai=random.choice([Monster.AI_IDLE, Monster.AI_PATROL])
        )
        monsters.append(m)

    # Items
    n_items = random.randint(0, 2)
    valid_items = [t for t in ITEM_TEMPLATES if t[6] <= depth]
    if not valid_items:
        valid_items = ITEM_TEMPLATES[:3]

    for _ in range(n_items):
        ix = random.randint(room.x1, room.x2 - 1)
        iy = random.randint(room.y1, room.y2 - 1)
        if not tiles[iy][ix].walkable:
            continue
        weights = [t[7] for t in valid_items]
        tpl = random.choices(valid_items, weights=weights)[0]
        val = tpl[2] if tpl[1] != 'gold' else random.randint(5 * depth, 20 * depth)
        item = Item(tpl[1], val, tpl[0], tpl[3], tpl[4])
        items.append((ix, iy, item))


# ─────────────────────────── Field of View ───────────────────────

def compute_fov(tiles, ox, oy, radius):
    visible = set()
    visible.add((ox, oy))

    for angle_i in range(360):
        angle = math.radians(angle_i)
        dx = math.cos(angle)
        dy = math.sin(angle)
        rx, ry = float(ox), float(oy)
        for _ in range(radius):
            rx += dx
            ry += dy
            ix, iy = int(round(rx)), int(round(ry))
            if ix < 0 or ix >= MAP_W or iy < 0 or iy >= MAP_H:
                break
            visible.add((ix, iy))
            if not tiles[iy][ix].transparent:
                break
    return visible


# ─────────────────────────── Combat ──────────────────────────────

def attack(attacker_power, defender_defense):
    dmg = attacker_power - defender_defense
    dmg = max(1, dmg + random.randint(-2, 2))
    return dmg


# ─────────────────────────── AI ──────────────────────────────────

def bfs_step(tiles, sx, sy, tx, ty, monsters):
    blocked = {(m.x, m.y) for m in monsters if (m.x, m.y) != (sx, sy)}
    queue = deque()
    queue.append((sx, sy, None))
    visited = {(sx, sy)}
    dirs = [(0,-1),(0,1),(-1,0),(1,0)]

    while queue:
        x, y, first = queue.popleft()
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if nx < 0 or nx >= MAP_W or ny < 0 or ny >= MAP_H:
                continue
            if not tiles[ny][nx].walkable:
                continue
            if (nx, ny) in blocked:
                continue
            step = first if first else (nx, ny)
            if (nx, ny) == (tx, ty):
                return step
            visited.add((nx, ny))
            queue.append((nx, ny, step))
    return None


def monster_turn(monster, player, tiles, monsters, messages):
    if not monster.is_alive():
        return

    dist = abs(monster.x - player.x) + abs(monster.y - player.y)

    # Detect player
    if dist <= monster.alert_range:
        monster.ai_state = Monster.AI_CHASE

    if monster.ai_state == Monster.AI_CHASE:
        if dist == 1:
            dmg = attack(monster.fighter.power, player.total_defense)
            player.fighter.hp -= dmg
            messages.append(f"{monster.name} 攻击你！造成 {dmg} 点伤害", 'red')
        else:
            step = bfs_step(tiles, monster.x, monster.y, player.x, player.y, monsters)
            if step:
                monster.x, monster.y = step

    elif monster.ai_state == Monster.AI_PATROL:
        # Random walk
        if random.random() < 0.4:
            dirs = [(0,-1),(0,1),(-1,0),(1,0)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = monster.x + dx, monster.y + dy
                if tiles[ny][nx].walkable and not any(m.x == nx and m.y == ny for m in monsters if m is not monster):
                    if not (nx == player.x and ny == player.y):
                        monster.x, monster.y = nx, ny
                        break


# ─────────────────────────── Message Log ─────────────────────────

class MessageLog:
    def __init__(self, max_lines=6):
        self.messages = []  # (text, color_key)
        self.max_lines = max_lines

    def append(self, text, color='white'):
        self.messages.append((text, color))
        if len(self.messages) > 60:
            self.messages.pop(0)

    def recent(self):
        return self.messages[-self.max_lines:]


# ─────────────────────────── Rendering ───────────────────────────

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1,  curses.COLOR_WHITE,   -1)   # white
    curses.init_pair(2,  curses.COLOR_YELLOW,  -1)   # yellow
    curses.init_pair(3,  curses.COLOR_GREEN,   -1)   # green
    curses.init_pair(4,  curses.COLOR_RED,     -1)   # red
    curses.init_pair(5,  curses.COLOR_CYAN,    -1)   # cyan
    curses.init_pair(6,  curses.COLOR_MAGENTA, -1)   # magenta
    curses.init_pair(7,  curses.COLOR_BLUE,    -1)   # blue
    curses.init_pair(8,  curses.COLOR_BLACK,   -1)   # dark (explored)
    curses.init_pair(9,  curses.COLOR_WHITE,   curses.COLOR_RED)   # hp bar
    curses.init_pair(10, curses.COLOR_BLACK,   curses.COLOR_WHITE) # ui bg

    global COLORS
    COLORS = {
        'white':     curses.color_pair(1),
        'white_bold':curses.color_pair(1) | curses.A_BOLD,
        'yellow':    curses.color_pair(2),
        'yellow_bold':curses.color_pair(2) | curses.A_BOLD,
        'green':     curses.color_pair(3),
        'brown':     curses.color_pair(2),   # approximate
        'red':       curses.color_pair(4),
        'red_bold':  curses.color_pair(4) | curses.A_BOLD,
        'cyan':      curses.color_pair(5),
        'magenta':   curses.color_pair(6),
        'blue':      curses.color_pair(7),
        'dark':      curses.color_pair(8),
        'wall':      curses.color_pair(8)  | curses.A_DIM,
        'floor':     curses.color_pair(8)  | curses.A_DIM,
        'door':      curses.color_pair(2),
        'stair':     curses.color_pair(2)  | curses.A_BOLD,
        'ui':        curses.color_pair(10),
        'hp_bar':    curses.color_pair(9),
    }


TILE_VIS_COLOR = {
    'wall':  'white',
    'floor': 'dark',
    'door':  'yellow',
    'stair': 'yellow_bold',
}


def render(stdscr, player, tiles, monsters, items, fov, messages, depth, camera_x, camera_y):
    sh, sw = stdscr.getmaxyx()
    map_h = sh - 9   # reserve bottom for UI
    map_w = sw

    stdscr.erase()

    # ── Map ──
    for sy in range(map_h):
        for sx in range(map_w):
            tx = sx + camera_x
            ty = sy + camera_y
            if tx < 0 or tx >= MAP_W or ty < 0 or ty >= MAP_H:
                continue
            tile = tiles[ty][tx]
            in_fov = (tx, ty) in fov

            if in_fov:
                tile.explored = True
                cname = TILE_VIS_COLOR.get(tile.color, 'white')
                # Brighten visible tiles
                attr = COLORS.get(cname, COLORS['white'])
                if tile.color == 'floor':
                    attr = COLORS['dark']
                elif tile.color == 'wall':
                    attr = COLORS['white'] | curses.A_DIM
                else:
                    attr = COLORS.get(cname, COLORS['white'])
                try:
                    stdscr.addch(sy, sx, tile.glyph, attr)
                except curses.error:
                    pass
            elif tile.explored:
                try:
                    stdscr.addch(sy, sx, tile.glyph, COLORS['wall'])
                except curses.error:
                    pass

    # ── Items ──
    for (ix, iy, item) in items:
        sx, sy = ix - camera_x, iy - camera_y
        if (ix, iy) in fov and 0 <= sx < map_w and 0 <= sy < map_h:
            attr = COLORS.get(item.color, COLORS['yellow'])
            try:
                stdscr.addch(sy, sx, item.glyph, attr)
            except curses.error:
                pass

    # ── Monsters ──
    for m in monsters:
        if not m.is_alive():
            continue
        sx, sy = m.x - camera_x, m.y - camera_y
        if (m.x, m.y) in fov and 0 <= sx < map_w and 0 <= sy < map_h:
            attr = COLORS.get(m.color, COLORS['red']) | curses.A_BOLD
            try:
                stdscr.addch(sy, sx, m.glyph, attr)
            except curses.error:
                pass

    # ── Player ──
    px, py = player.x - camera_x, player.y - camera_y
    if 0 <= px < map_w and 0 <= py < map_h:
        try:
            stdscr.addch(py, px, '@', COLORS['white_bold'])
        except curses.error:
            pass

    # ── HUD ──
    ui_y = map_h
    # Separator
    try:
        stdscr.addstr(ui_y, 0, '─' * sw, COLORS['dark'])
    except curses.error:
        pass

    # Stats line
    hp = player.fighter.hp
    mhp = player.fighter.max_hp
    hp_bar_w = 12
    hp_filled = int(hp_bar_w * hp / max(mhp, 1))
    hp_bar = '█' * hp_filled + '░' * (hp_bar_w - hp_filled)
    hp_color = COLORS['green'] if hp > mhp * 0.6 else (COLORS['yellow'] if hp > mhp * 0.3 else COLORS['red'])

    stats = (
        f" 勇者 Lv.{player.level}  "
        f"HP:"
    )
    try:
        stdscr.addstr(ui_y + 1, 0, stats, COLORS['white'])
        stdscr.addstr(hp_bar, hp_color)
        stdscr.addstr(f" {hp}/{mhp}  ", COLORS['white'])
        stdscr.addstr(f"MP:{player.mp}/{player.max_mp}  ", COLORS['cyan'])
        stdscr.addstr(f"ATK:{player.total_power}  DEF:{player.total_defense}  ", COLORS['yellow'])
        stdscr.addstr(f"XP:{player.xp}/{player.xp_next}  ", COLORS['green'])
        stdscr.addstr(f"金:{player.gold}  ", COLORS['yellow_bold'])
        stdscr.addstr(f"地下{depth}层  ", COLORS['magenta'])
        weapon = player.weapon.name if player.weapon else '徒手'
        armor  = player.armor.name  if player.armor  else '无甲'
        stdscr.addstr(f"武:{weapon} 甲:{armor}", COLORS['cyan'])
    except curses.error:
        pass

    # Message log
    recent = messages.recent()
    msg_colors = {'red': COLORS['red'], 'green': COLORS['green'],
                  'yellow': COLORS['yellow'], 'cyan': COLORS['cyan'],
                  'white': COLORS['white'], 'magenta': COLORS['magenta']}
    for i, (text, color) in enumerate(recent):
        row = ui_y + 2 + i
        if row >= sh:
            break
        attr = msg_colors.get(color, COLORS['white'])
        try:
            stdscr.addstr(row, 1, text[:sw - 2], attr)
        except curses.error:
            pass

    # Key hints
    hint = " [WASD]移动 [G]拾取 [I]背包 [U]使用 [>/< ]楼梯 [Q]退出"
    try:
        stdscr.addstr(sh - 1, 0, hint[:sw], COLORS['dark'])
    except curses.error:
        pass

    stdscr.refresh()


# ─────────────────────────── Inventory Screen ────────────────────

def show_inventory(stdscr, player, messages):
    sh, sw = stdscr.getmaxyx()
    while True:
        stdscr.clear()
        title = "═══ 背包 ═══"
        try:
            stdscr.addstr(0, sw // 2 - len(title) // 2, title, COLORS['yellow_bold'])
        except curses.error:
            pass

        if not player.inventory:
            try:
                stdscr.addstr(2, 2, "背包是空的", COLORS['white'])
            except curses.error:
                pass
        else:
            for i, item in enumerate(player.inventory):
                marker = ''
                if item == player.weapon:
                    marker = ' [装备中-武器]'
                elif item == player.armor:
                    marker = ' [装备中-护甲]'
                line = f" {i+1}. {item.glyph} {item.name}{marker}  ({item.kind})"
                attr = COLORS.get(item.color, COLORS['white'])
                try:
                    stdscr.addstr(2 + i, 1, line[:sw - 2], attr)
                except curses.error:
                    pass

        equipped = []
        if player.weapon:
            equipped.append(f"武器: {player.weapon.name} +{player.weapon.value}ATK")
        if player.armor:
            equipped.append(f"护甲: {player.armor.name} +{player.armor.value}DEF")

        row = 2 + max(len(player.inventory), 1) + 1
        for e in equipped:
            try:
                stdscr.addstr(row, 2, e, COLORS['cyan'])
                row += 1
            except curses.error:
                pass

        try:
            stdscr.addstr(row + 1, 2, "[数字键]使用/装备  [D]丢弃  [ESC/I]关闭", COLORS['dark'])
        except curses.error:
            pass

        stdscr.refresh()
        key = stdscr.getch()

        if key in (27, ord('i'), ord('I')):
            return

        if ord('1') <= key <= ord('9'):
            idx = key - ord('1')
            if idx < len(player.inventory):
                use_item(player, idx, messages)

        if key in (ord('d'), ord('D')) and player.inventory:
            idx_input = get_number_input(stdscr, sh - 2, 2, "丢弃哪个? (数字): ", sw)
            if idx_input is not None and 0 <= idx_input < len(player.inventory):
                dropped = player.inventory.pop(idx_input)
                if dropped == player.weapon:
                    player.weapon = None
                if dropped == player.armor:
                    player.armor = None
                messages.append(f"丢掉了 {dropped.name}", 'white')


def get_number_input(stdscr, y, x, prompt, max_w):
    try:
        stdscr.addstr(y, x, prompt, COLORS['yellow'])
        stdscr.refresh()
    except curses.error:
        pass
    curses.echo()
    curses.curs_set(1)
    buf = ""
    while True:
        key = stdscr.getch()
        if key in (10, 13):
            break
        if key == 27:
            buf = ""
            break
        if ord('0') <= key <= ord('9'):
            buf += chr(key)
            if len(buf) > 2:
                break
    curses.noecho()
    curses.curs_set(0)
    try:
        return int(buf) - 1
    except ValueError:
        return None


def use_item(player, idx, messages):
    item = player.inventory[idx]
    if item.kind == 'potion_hp':
        healed = min(item.value, player.fighter.max_hp - player.fighter.hp)
        player.fighter.hp += healed
        messages.append(f"喝下 {item.name}，恢复 {healed} HP", 'green')
        player.inventory.pop(idx)
    elif item.kind == 'potion_mp':
        restored = min(item.value, player.max_mp - player.mp)
        player.mp += restored
        messages.append(f"喝下 {item.name}，恢复 {restored} MP", 'cyan')
        player.inventory.pop(idx)
    elif item.kind == 'weapon':
        old = player.weapon
        player.weapon = item
        player.inventory.pop(idx)
        if old:
            player.inventory.append(old)
        messages.append(f"装备了 {item.name} (+{item.value} ATK)", 'yellow')
    elif item.kind == 'armor':
        old = player.armor
        player.armor = item
        player.inventory.pop(idx)
        if old:
            player.inventory.append(old)
        messages.append(f"装备了 {item.name} (+{item.value} DEF)", 'yellow')
    elif item.kind == 'scroll':
        messages.append(f"使用 {item.name}！造成 {item.value} 点闪电伤害！", 'cyan')
        # TODO: target nearest monster
        player.inventory.pop(idx)
    elif item.kind == 'gold':
        messages.append(f"已经是金币了", 'yellow')


# ─────────────────────────── Death / Win ─────────────────────────

def death_screen(stdscr, player, depth):
    stdscr.clear()
    sh, sw = stdscr.getmaxyx()
    lines = [
        "★  你已阵亡  ★",
        "",
        f"  到达第 {depth} 层",
        f"  消灭 {player.kills} 个敌人",
        f"  积累 {player.gold} 金币",
        f"  达到 {player.level} 级",
        "",
        "  [R] 重新开始   [Q] 退出",
    ]
    r = sh // 2 - len(lines) // 2
    for i, line in enumerate(lines):
        c = max(0, sw // 2 - len(line) // 2)
        attr = COLORS['red'] | curses.A_BOLD if i == 0 else COLORS['white']
        try:
            stdscr.addstr(r + i, c, line, attr)
        except curses.error:
            pass
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord('r'), ord('R')):
            return 'restart'
        if key in (ord('q'), ord('Q')):
            return 'quit'


def win_screen(stdscr, player):
    stdscr.clear()
    sh, sw = stdscr.getmaxyx()
    lines = [
        "✦  恭喜！你征服了地牢！  ✦",
        "",
        f"  消灭 {player.kills} 个敌人",
        f"  积累 {player.gold} 金币",
        f"  达到 {player.level} 级",
        "",
        "  [Q] 退出",
    ]
    r = sh // 2 - len(lines) // 2
    for i, line in enumerate(lines):
        c = max(0, sw // 2 - len(line) // 2)
        attr = COLORS['yellow_bold'] if i == 0 else COLORS['white']
        try:
            stdscr.addstr(r + i, c, line, attr)
        except curses.error:
            pass
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            return


# ─────────────────────────── Title Screen ────────────────────────

def title_screen(stdscr):
    stdscr.clear()
    sh, sw = stdscr.getmaxyx()
    art = [
        "  ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗",
        "  ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗████╗  ██║",
        "  ██║  ██║██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║██╔██╗ ██║",
        "  ██║  ██║██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║██║╚██╗██║",
        "  ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝██║ ╚████║",
        "  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝",
        "",
        "          地  牢  探  险  ─  Roguelike  Dungeon  Crawler",
        "",
        "  你是一位勇敢的冒险者，踏入了充满危险的地牢深处…",
        "  杀死敌人获取经验，拾取装备提升战力，一路向下寻找传说中的宝藏！",
        "",
        "  ┌─────────────────────────────────────────────┐",
        "  │  WASD / 方向键 = 移动       G = 拾取物品    │",
        "  │  I = 打开背包               U = 使用物品    │",
        "  │  > = 下楼梯                 < = 上楼梯      │",
        "  │  Q = 退出游戏                               │",
        "  └─────────────────────────────────────────────┘",
        "",
        "               按 任意键 开始游戏…",
    ]
    start_r = max(0, sh // 2 - len(art) // 2)
    for i, line in enumerate(art):
        r = start_r + i
        c = max(0, sw // 2 - len(line) // 2)
        if i == 0:
            attr = COLORS['yellow_bold']
        elif i == 7:
            attr = COLORS['cyan'] | curses.A_BOLD
        elif i in (9, 10):
            attr = COLORS['white']
        elif i == len(art) - 1:
            attr = COLORS['green'] | curses.A_BOLD
        else:
            attr = COLORS['dark']
        try:
            stdscr.addstr(r, c, line[:sw], attr)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.getch()


# ─────────────────────────── Main Game Loop ──────────────────────

def run_game(stdscr):
    init_colors()
    curses.curs_set(0)
    stdscr.keypad(True)

    title_screen(stdscr)

    while True:
        result = play_game(stdscr)
        if result == 'restart':
            continue
        else:
            break


def play_game(stdscr):
    depth = 1
    player = Player(0, 0)
    messages = MessageLog()

    tiles, rooms, monsters, items, sx, sy = generate_map(depth)
    player.x, player.y = sx, sy

    messages.append("欢迎来到地牢！寻找下楼梯(>)深入地下…", 'yellow')
    messages.append(f"当前武器: 徒手  防具: 无甲  用G拾取物品", 'cyan')

    sh, sw = stdscr.getmaxyx()
    map_h = sh - 9

    stdscr.nodelay(False)

    while True:
        # Camera: center on player, clamped to map
        camera_x = max(0, min(player.x - sw // 2, MAP_W - sw))
        camera_y = max(0, min(player.y - map_h // 2, MAP_H - map_h))

        fov = compute_fov(tiles, player.x, player.y, FOV_RADIUS)

        render(stdscr, player, tiles, monsters, items, fov, messages, depth, camera_x, camera_y)

        key = stdscr.getch()

        # Direction
        move_dir = None
        if key in (curses.KEY_UP,    ord('w'), ord('W')): move_dir = (0, -1)
        elif key in (curses.KEY_DOWN, ord('s'), ord('S')): move_dir = (0,  1)
        elif key in (curses.KEY_LEFT, ord('a'), ord('A')): move_dir = (-1, 0)
        elif key in (curses.KEY_RIGHT,ord('d'), ord('D')): move_dir = (1,  0)

        if move_dir:
            nx, ny = player.x + move_dir[0], player.y + move_dir[1]
            if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                # Check monster
                target = next((m for m in monsters if m.x == nx and m.y == ny and m.is_alive()), None)
                if target:
                    dmg = attack(player.total_power, target.fighter.defense)
                    target.fighter.hp -= dmg
                    if target.is_alive():
                        messages.append(f"攻击 {target.name} 造成 {dmg} 伤害 (剩余HP:{target.fighter.hp})", 'yellow')
                    else:
                        messages.append(f"击败了 {target.name}！获得 {target.fighter.xp_value} XP", 'green')
                        player.xp += target.fighter.xp_value
                        player.kills += 1
                        # Gold drop
                        gold = random.randint(1, depth * 3)
                        player.gold += gold
                        messages.append(f"  获得 {gold} 金币", 'yellow')
                        # Level up check
                        while player.xp >= player.xp_next:
                            msg = player.level_up()
                            messages.append(msg, 'cyan')
                elif tiles[ny][nx].walkable:
                    player.x, player.y = nx, ny
                    # Auto-pickup gold
                    for entry in items[:]:
                        ix, iy, item = entry
                        if ix == nx and iy == ny and item.kind == 'gold':
                            player.gold += item.value
                            messages.append(f"拾取了 {item.value} 金币", 'yellow')
                            items.remove(entry)

        # Pickup
        elif key in (ord('g'), ord('G')):
            picked = [(i, e) for i, e in enumerate(items) if e[0] == player.x and e[1] == player.y and e[2].kind != 'gold']
            if not picked:
                messages.append("这里没有可拾取的物品", 'white')
            elif len(player.inventory) >= player.max_inventory:
                messages.append("背包已满！", 'red')
            else:
                _, entry = picked[0]
                item = entry[2]
                player.inventory.append(item)
                items.remove(entry)
                messages.append(f"拾取了 {item.name}", 'green')

        # Inventory
        elif key in (ord('i'), ord('I')):
            show_inventory(stdscr, player, messages)
            continue  # skip monster turn

        # Use item shortcut
        elif key in (ord('u'), ord('U')):
            if player.inventory:
                show_inventory(stdscr, player, messages)
            else:
                messages.append("背包是空的", 'white')
            continue

        # Stairs down
        elif key == ord('>'):
            tile = tiles[player.y][player.x]
            if tile.glyph == '>':
                if depth >= MAX_DEPTH:
                    win_screen(stdscr, player)
                    return 'quit'
                depth += 1
                player.deepest_floor = max(player.deepest_floor, depth)
                tiles, rooms, monsters, items, sx, sy = generate_map(depth)
                player.x, player.y = sx, sy
                messages.append(f"你下到了第 {depth} 层… 危险在增加！", 'magenta')
            else:
                messages.append("这里没有下楼梯", 'white')
            continue

        # Stairs up
        elif key == ord('<'):
            tile = tiles[player.y][player.x]
            if tile.glyph == '<':
                if depth <= 1:
                    messages.append("你已在最顶层", 'white')
                else:
                    depth -= 1
                    tiles, rooms, monsters, items, sx, sy = generate_map(depth)
                    player.x, player.y = sx, sy
                    messages.append(f"你回到了第 {depth} 层", 'white')
            else:
                messages.append("这里没有上楼梯", 'white')
            continue

        # Quit
        elif key in (ord('q'), ord('Q')):
            return 'quit'

        else:
            continue  # unrecognized key, skip monster turn

        # Monster turns
        alive_monsters = [m for m in monsters if m.is_alive()]
        for m in alive_monsters:
            monster_turn(m, player, tiles, alive_monsters, messages)

        # Check death
        if player.fighter.hp <= 0:
            fov = compute_fov(tiles, player.x, player.y, FOV_RADIUS)
            render(stdscr, player, tiles, monsters, items, fov, messages, depth, camera_x, camera_y)
            return death_screen(stdscr, player, depth)


# ─────────────────────────── Entry Point ─────────────────────────

if __name__ == '__main__':
    try:
        curses.wrapper(run_game)
    except KeyboardInterrupt:
        pass
    print("\n感谢游玩《地牢探险》！再见 👋\n")
