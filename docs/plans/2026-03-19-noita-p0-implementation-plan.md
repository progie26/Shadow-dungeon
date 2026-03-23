# Shadow Dungeon Noita-P0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Land the first playable Noita-inspired foundation (material reactions, wand compilation, route matrix) without breaking the existing roguelike loop.

**Architecture:** Keep `index.html` as the gameplay host, move deterministic Noita primitives into `src/noita-core.js`, and call them from the turn loop. This preserves current UX while enabling reaction-driven gameplay expansion.

**Tech Stack:** Vanilla JS, Canvas 2D, Node built-in test runner (`node:test`), no external dependencies.

---

## Delivered in this pass

- Added `src/noita-core.js`:
  - Deterministic reaction rules (`water + lava`, `oil + fire`)
  - Tick-based material simulation (`createMaterialSystem`)
  - Wand compiler with recursion protection and mana validation (`compileWand`)
  - Six-biome route skeleton (`buildRouteMatrix`)
- Added `tests/noita-core.test.cjs` with 6 tests covering:
  - Reaction behavior
  - Wand compile success path
  - Trigger recursion rejection
  - Route matrix shape
  - Deterministic tick processing
- Integrated P0 runtime in `index.html`:
  - Loads `src/noita-core.js`
  - Initializes material simulation each floor
  - Seeds oil/water/lava pools for environmental interaction
  - Applies material tick each player turn
  - Adds fire material from fireball path
  - Renders material overlays in map tiles
  - Logs route + wand compile status at run start

## Next tasks (P1)

### Task 1: Expand reaction table to 20 baseline rules

**Files:**
- Modify: `src/noita-core.js`
- Test: `tests/noita-core.test.cjs`

**Acceptance:**
- New reaction ids covered by tests
- No order-dependent test flakiness

### Task 2: Add reaction byproducts placement mechanics

**Files:**
- Modify: `src/noita-core.js`
- Modify: `index.html`
- Test: `tests/noita-core.test.cjs`

**Acceptance:**
- `steam` / `gas` byproducts can occupy adjacent cells
- Existing reactions remain deterministic

### Task 3: Add wand node caps and compile diagnostics

**Files:**
- Modify: `src/noita-core.js`
- Test: `tests/noita-core.test.cjs`

**Acceptance:**
- Reject casts above max expanded node count
- Error codes are stable and user-readable

### Task 4: Add in-run wand loadout UI card

**Files:**
- Modify: `index.html`

**Acceptance:**
- Player can inspect current cast plan
- Mana cost and trigger chain are visible

### Task 5: Add environment damage and resistance tags

**Files:**
- Modify: `index.html`
- Modify: `src/noita-core.js`
- Test: `tests/noita-core.test.cjs`

**Acceptance:**
- Burning/lava/acid damage hooks into combat pipeline
- Class-specific mitigation can be configured

## Verification commands

```bash
node --test tests/noita-core.test.cjs
python -m http.server 4173 --directory D:/Opencode/Shadow-dungeon
```

Open `http://127.0.0.1:4173/index.html`, start game, verify Noita initialization logs appear and material overlays render.

## Art asset drop-in workflow

P1 adds optional image hooks in `index.html`. To use your provided concept art, place files under `assets/art/` with these names:

- `assets/art/hero-warrior.png`
- `assets/art/hero-mage.png`
- `assets/art/hero-rogue.png`
- `assets/art/boss-dragon.png`
- `assets/art/boss-lord.png`

Behavior:

- If files exist, class cards and boss preview card render them automatically.
- If files are missing, UI falls back gracefully (image blocks are hidden, gameplay unaffected).

Enable switch:

- In `index.html`, set `ART_ASSETS.enabled = true` after files are prepared.
