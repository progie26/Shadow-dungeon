# Art Asset Overrides

The game now ships with built-in SVG rune-totem placeholder art generated in `src/noita-art.js`.
You do not need external files for heroes, enemies, or bosses anymore.

If you want to replace the generated SVG later, keep the same role mapping and update `ART_ASSETS` in `index.html` or `buildTotemArtManifest()` in `src/noita-art.js`.

Current built-in roles:

- `warrior` - shield totem
- `mage` - rune orb totem
- `rogue` - dagger totem
- `skeleton` - bone fang totem
- `cultist` - hooded rune totem
- `rogue` - stealth dagger totem (enemy role)
- `wraith` - ghost orb totem
- `boss_dragon` - bone dragon totem
- `boss_lord` - shadow crown totem

Recommended future override workflow:

1. Keep the same semantic role names
2. Swap `src` values to your final art asset URLs or data URIs
3. Preserve the dark, cute, abstract silhouette language
