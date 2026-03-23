'use strict';

const REACTION_RULES = [
  {
    id: 'water_lava',
    priority: 90,
    sourceMaterial: 'water',
    materials: ['water', 'lava'],
    nextMaterial: 'stone',
    byproduct: 'steam',
  },
  {
    id: 'oil_fire',
    priority: 80,
    sourceMaterial: 'oil',
    materials: ['oil', 'fire'],
    nextMaterial: 'burning_oil',
    byproduct: null,
  },
  { id: 'water_fire', priority: 88, sourceMaterial: 'water', materials: ['water', 'fire'], nextMaterial: 'steam', byproduct: null },
  { id: 'ice_fire', priority: 84, sourceMaterial: 'ice', materials: ['ice', 'fire'], nextMaterial: 'water', byproduct: null },
  { id: 'poison_fire', priority: 83, sourceMaterial: 'poison', materials: ['poison', 'fire'], nextMaterial: 'toxic_smoke', byproduct: null },
  { id: 'acid_metal', priority: 82, sourceMaterial: 'acid', materials: ['acid', 'metal'], nextMaterial: 'corrosive_acid', byproduct: 'toxic_smoke' },
  { id: 'water_electric', priority: 81, sourceMaterial: 'water', materials: ['water', 'electric'], nextMaterial: 'charged_water', byproduct: null },
  { id: 'oil_lava', priority: 80, sourceMaterial: 'oil', materials: ['oil', 'lava'], nextMaterial: 'burning_oil', byproduct: 'smoke' },
  { id: 'blood_fire', priority: 79, sourceMaterial: 'blood', materials: ['blood', 'fire'], nextMaterial: 'blood_steam', byproduct: null },
  { id: 'steam_cold', priority: 78, sourceMaterial: 'steam', materials: ['steam', 'ice'], nextMaterial: 'water', byproduct: null },
  { id: 'toxic_water_fire', priority: 77, sourceMaterial: 'toxic_water', materials: ['toxic_water', 'fire'], nextMaterial: 'steam', byproduct: 'toxic_smoke' },
  { id: 'lava_water', priority: 76, sourceMaterial: 'lava', materials: ['lava', 'water'], nextMaterial: 'stone', byproduct: 'steam' },
  { id: 'burning_oil_water', priority: 75, sourceMaterial: 'burning_oil', materials: ['burning_oil', 'water'], nextMaterial: 'oil', byproduct: 'steam' },
  { id: 'acid_water', priority: 74, sourceMaterial: 'acid', materials: ['acid', 'water'], nextMaterial: 'toxic_water', byproduct: null },
  { id: 'oil_acid', priority: 73, sourceMaterial: 'oil', materials: ['oil', 'acid'], nextMaterial: 'corrupted_oil', byproduct: null },
  { id: 'charged_water_fire', priority: 72, sourceMaterial: 'charged_water', materials: ['charged_water', 'fire'], nextMaterial: 'steam', byproduct: 'electric' },
  { id: 'smoke_ice', priority: 71, sourceMaterial: 'smoke', materials: ['smoke', 'ice'], nextMaterial: 'air', byproduct: 'water' },
  { id: 'blood_acid', priority: 70, sourceMaterial: 'blood', materials: ['blood', 'acid'], nextMaterial: 'toxic_water', byproduct: null },
  { id: 'corrupted_oil_fire', priority: 69, sourceMaterial: 'corrupted_oil', materials: ['corrupted_oil', 'fire'], nextMaterial: 'burning_oil', byproduct: 'toxic_smoke' },
  { id: 'steam_lava', priority: 68, sourceMaterial: 'steam', materials: ['steam', 'lava'], nextMaterial: 'smoke', byproduct: null },
  { id: 'toxic_smoke_fire', priority: 67, sourceMaterial: 'toxic_smoke', materials: ['toxic_smoke', 'fire'], nextMaterial: 'smoke', byproduct: null },
];

const CARDINAL = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

const BASE_SPELLS = {
  firebolt: { mana: 20 },
  spark: { mana: 10 },
};

const MODIFIERS = {
  triple_cast: { mana: 15, multi: 3 },
};

const TRIGGERS = {
  on_hit_cast: { mana: 10 },
};

function inBounds(grid, x, y) {
  return y >= 0 && y < grid.length && x >= 0 && x < (grid[0] ? grid[0].length : 0);
}

function cloneGrid(grid) {
  return grid.map((row) => row.slice());
}

function findReaction(source, neighbor) {
  let selected = null;
  for (const rule of REACTION_RULES) {
    if (rule.sourceMaterial && rule.sourceMaterial !== source) continue;
    const hasSource = rule.materials.includes(source);
    const hasNeighbor = rule.materials.includes(neighbor);
    if (!hasSource || !hasNeighbor) continue;
    if (!selected || rule.priority > selected.priority) {
      selected = rule;
    }
  }
  return selected;
}

function applySingleCellReaction(grid, x, y) {
  if (!inBounds(grid, x, y)) {
    return { nextMaterial: null, byproduct: null, triggeredRule: null };
  }

  const source = grid[y][x];
  let best = null;
  let bestNeighbor = null;

  for (const [dx, dy] of CARDINAL) {
    const nx = x + dx;
    const ny = y + dy;
    if (!inBounds(grid, nx, ny)) continue;
    const neighbor = grid[ny][nx];
    const rule = findReaction(source, neighbor);
    if (!rule) continue;
    if (!best || rule.priority > best.priority) {
      best = rule;
      bestNeighbor = { x: nx, y: ny };
    }
  }

  if (!best) {
    return { nextMaterial: source, byproduct: null, triggeredRule: null };
  }

  return {
    nextMaterial: best.nextMaterial,
    byproduct: best.byproduct,
    triggeredRule: best.id,
    neighborX: bestNeighbor.x,
    neighborY: bestNeighbor.y,
  };
}

function placeByproduct(snapshot, next, sourceX, sourceY, neighborX, neighborY, byproduct) {
  if (!byproduct) return false;
  const anchors = [
    [sourceX, sourceY],
    [neighborX, neighborY],
  ];

  for (const [ax, ay] of anchors) {
    for (const [dx, dy] of CARDINAL) {
      const x = ax + dx;
      const y = ay + dy;
      if (!inBounds(snapshot, x, y)) continue;
      if (snapshot[y][x] !== 'air') continue;
      if (next[y][x] !== 'air') continue;
      next[y][x] = byproduct;
      return true;
    }
  }
  return false;
}

function createMaterialSystem(config) {
  const width = config.width;
  const height = config.height;
  const initial = config.initial || [];
  const grid = Array.from({ length: height }, (_, y) =>
    Array.from({ length: width }, (_, x) => (initial[y] && initial[y][x]) || 'air')
  );

  return {
    tick() {
      const snapshot = cloneGrid(grid);
      const next = cloneGrid(grid);
      let reactionsProcessed = 0;
      let byproductsCreated = 0;

      for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
          const out = applySingleCellReaction(snapshot, x, y);
          if (out.triggeredRule && out.nextMaterial !== snapshot[y][x]) {
            next[y][x] = out.nextMaterial;
            reactionsProcessed += 1;
            if (placeByproduct(snapshot, next, x, y, out.neighborX, out.neighborY, out.byproduct)) {
              byproductsCreated += 1;
            }
          }
        }
      }

      for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
          grid[y][x] = next[y][x];
        }
      }

      return { reactionsProcessed, byproductsCreated };
    },
    get(x, y) {
      if (!inBounds(grid, x, y)) return 'void';
      return grid[y][x];
    },
    set(x, y, material) {
      if (!inBounds(grid, x, y)) return false;
      grid[y][x] = material;
      return true;
    },
    dump() {
      return cloneGrid(grid);
    },
  };
}

function compileWand(input, options = {}) {
  const manaBudget = input && typeof input.mana === 'number' ? input.mana : 0;
  const slots = input && Array.isArray(input.slots) ? input.slots : [];
  const maxExpandedNodes = typeof options.maxExpandedNodes === 'number' ? options.maxExpandedNodes : 24;

  const state = {
    baseSpellsRaw: [],
    baseProjectiles: [],
    onHit: [],
    manaCost: 0,
    castMultiplier: 1,
  };

  const chainSeen = new Set();

  function compileNode(node, insideTrigger) {
    if (!node || typeof node !== 'object') {
      return { ok: false, error: { code: 'INVALID_NODE', message: 'Invalid wand node' } };
    }

    if (chainSeen.has(node)) {
      return { ok: false, error: { code: 'TRIGGER_RECURSION', message: 'Recursive trigger chain detected' } };
    }

    if (node.kind === 'base') {
      const base = BASE_SPELLS[node.id];
      if (!base) return { ok: false, error: { code: 'UNKNOWN_BASE', message: `Unknown base spell: ${node.id}` } };
      state.manaCost += base.mana;
      if (insideTrigger) {
        state.onHit.push(node.id);
      } else {
        state.baseSpellsRaw.push(node.id);
      }
      return { ok: true };
    }

    if (node.kind === 'modifier') {
      const mod = MODIFIERS[node.id];
      if (!mod) return { ok: false, error: { code: 'UNKNOWN_MODIFIER', message: `Unknown modifier: ${node.id}` } };
      state.manaCost += mod.mana;
      if (mod.multi) state.castMultiplier = mod.multi;
      return { ok: true };
    }

    if (node.kind === 'trigger') {
      const trig = TRIGGERS[node.id];
      if (!trig) return { ok: false, error: { code: 'UNKNOWN_TRIGGER', message: `Unknown trigger: ${node.id}` } };
      state.manaCost += trig.mana;

      chainSeen.add(node);
      const payload = Array.isArray(node.payload) ? node.payload : [];
      for (const child of payload) {
        const r = compileNode(child, true);
        if (!r.ok) return r;
      }
      chainSeen.delete(node);
      return { ok: true };
    }

    return { ok: false, error: { code: 'UNKNOWN_NODE_KIND', message: `Unknown node kind: ${node.kind}` } };
  }

  for (const node of slots) {
    const r = compileNode(node, false);
    if (!r.ok) return r;
  }

  for (const baseId of state.baseSpellsRaw) {
    for (let i = 0; i < state.castMultiplier; i += 1) {
      state.baseProjectiles.push(baseId);
    }
  }

  const expandedNodeCount = state.baseProjectiles.length + state.onHit.length;

  if (expandedNodeCount > maxExpandedNodes) {
    return {
      ok: false,
      error: {
        code: 'CAST_PLAN_TOO_LARGE',
        message: `Expanded cast nodes ${expandedNodeCount} exceeds cap ${maxExpandedNodes}`,
      },
      diagnostics: {
        expandedNodeCount,
        maxExpandedNodes,
      },
    };
  }

  if (state.manaCost > manaBudget) {
    return {
      ok: false,
      error: {
        code: 'MANA_OVER_BUDGET',
        message: `Mana cost ${state.manaCost} exceeds budget ${manaBudget}`,
      },
      diagnostics: {
        expandedNodeCount,
        maxExpandedNodes,
      },
    };
  }

  return {
    ok: true,
    castPlan: {
      baseProjectiles: state.baseProjectiles,
      onHit: state.onHit,
      totalManaCost: state.manaCost,
    },
    diagnostics: {
      expandedNodeCount,
      maxExpandedNodes,
    },
  };
}

function buildRouteMatrix() {
  const names = [
    'forgotten_dungeon',
    'weeping_graveyard',
    'abyss_rift',
    'molten_core',
    'eternal_winter',
    'shadow_throne',
  ];

  const unlockRules = [
    'collect_jailer_keys',
    'purify_curse_obelisk',
    'stabilize_rift_anchor',
    'disable_forge_valves',
    'ignite_three_ice_beacons',
    'gather_five_seals',
  ];

  return {
    mainline: names.map((name, idx) => ({
      id: name,
      unlockRule: unlockRules[idx],
      sideBranches: [
        `${name}_side_a`,
        `${name}_side_b`,
      ],
      hiddenLoop: {
        id: `${name}_hidden_loop`,
        unlockCondition: `trigger_${name}_secret`,
      },
    })),
  };
}

const NoitaCore = {
  REACTION_RULES,
  createMaterialSystem,
  applySingleCellReaction,
  compileWand,
  buildRouteMatrix,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = NoitaCore;
}

if (typeof window !== 'undefined') {
  window.NoitaCore = NoitaCore;
}
