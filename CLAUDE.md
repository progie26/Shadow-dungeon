# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**地牢探险 (Dungeon Explorer)** — A roguelike dungeon crawler with two independent implementations:

- `roguelike.py` — Terminal version using Python `curses`
- `index.html` — Web version using HTML5 Canvas + vanilla JavaScript

Both versions share the same gameplay design: procedurally generated floors, turn-based combat, FOV, BFS pathfinding AI, inventory, and 6 dungeon depths.

## Development Setup

No dependencies or build steps required.

**Terminal version** requires Python 3 and a terminal that supports curses (Linux/macOS):
```bash
python3 roguelike.py
```

**Web version** — open directly in a browser:
```bash
# Any static file server works, e.g.:
python3 -m http.server 8000
# then open http://localhost:8000/index.html
```
Or just open `index.html` directly as a local file.

## Common Commands

```bash
python3 roguelike.py        # Run terminal game
python3 -m http.server 8000 # Serve web version locally
```

## Code Style

- **Python**: Standard library only (`curses`, `random`, `math`, `collections`). No type annotations. Chinese strings for in-game text.
- **JavaScript**: Vanilla JS, no frameworks, no build tools. Global game state in `G`. Chinese strings for in-game text.
- Keep both implementations in sync when changing game rules (damage formula, level-up scaling, monster/item templates, map constants).

## Architecture

Both implementations follow the same structure:

| Component | Python (`roguelike.py`) | JavaScript (`index.html`) |
|---|---|---|
| Map gen | `generate_map()` — BSP-style room placement + L-shaped tunnels | `generateMap()` — same algorithm |
| FOV | `compute_fov()` — 360-ray casting | `computeFov()` — same |
| AI | `monster_turn()` + `bfs_step()` — idle/patrol/chase states | `monsterTurn()` + `bfsStep()` |
| Combat | `attack()` — `power - defense + rand(-2,2)`, min 1 | `calcDmg()` — same |
| Rendering | `curses` terminal | HTML5 Canvas (20px cells) |
| Input | Keyboard via `stdscr.getch()` | Keyboard events + D-pad buttons + swipe |

**Key constants** (must stay in sync across both files):
- `MAP_W=80/60`, `MAP_H=40`, `MAX_ROOMS=18/16`, `FOV_RADIUS=8`, `MAX_DEPTH=6`
- Player starts: HP 30, MP 10, ATK 5, DEF 2
- Level-up: HP+8, ATK+2, DEF+1; XP threshold scales ×1.6
