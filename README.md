# Shadow Dungeon / 暗影地牢

High-playability roguelike dungeon crawler for **web and mobile browsers**.

Live demo: https://progie26.github.io/shadow-dungeon/

## Highlights

- 8-floor procedural dungeon (rooms + corridors)
- 3 classes with unique skills: Warrior / Mage / Rogue
- Strong combat feedback: damage text, screen shake, hit flash, particles, combo bonus
- Equipment and affix system with rarity colors
- Random events: merchant, fountain, altar, trap, treasure
- Floor bosses with phase mechanics (Bone Dragon / Shadow Lord)
- Mobile-first controls: D-pad, skill buttons, swipe movement

## Controls

### Desktop

- Move: `WASD` or Arrow keys
- Skill 1/2: `1` / `2`
- Pickup: `G`
- Inventory: `I`
- Stairs: `>` or `<`
- Wait turn: `.`
- Toggle minimap: `M`

### Mobile

- Virtual D-pad to move
- Swipe on canvas to move
- Buttons for skills / pickup / inventory / stairs / minimap

## Run locally

No build tools required.

```bash
python -m http.server 4173
```

Open `http://127.0.0.1:4173/`.

## Tech stack

- Single-file `index.html`
- Vanilla JavaScript + Canvas 2D
- No external libraries or CDN dependencies

## Repository structure

- `index.html` - Full game implementation
- `docs/plans/2026-03-17-shadow-dungeon-design.md` - Design notes

## Roadmap ideas

- Save/load runs
- More classes and skills
- Additional biome themes
- Daily seed challenge mode
