const test = require('node:test');
const assert = require('node:assert/strict');

const {
  createMaterialSystem,
  applySingleCellReaction,
  compileWand,
  buildRouteMatrix,
} = require('../src/noita-core.js');

test('oil touching fire becomes burning_oil', () => {
  const grid = [
    ['oil', 'fire'],
  ];
  const out = applySingleCellReaction(grid, 0, 0);
  assert.equal(out.nextMaterial, 'burning_oil');
  assert.equal(out.triggeredRule, 'oil_fire');
});

test('water touching lava creates stone and steam by priority', () => {
  const grid = [
    ['water', 'lava'],
  ];
  const out = applySingleCellReaction(grid, 0, 0);
  assert.equal(out.nextMaterial, 'stone');
  assert.equal(out.byproduct, 'steam');
  assert.equal(out.triggeredRule, 'water_lava');
});

test('wand compiler expands trigger chain in deterministic order', () => {
  const result = compileWand({
    mana: 120,
    slots: [
      { kind: 'base', id: 'firebolt' },
      { kind: 'modifier', id: 'triple_cast' },
      { kind: 'trigger', id: 'on_hit_cast', payload: [{ kind: 'base', id: 'spark' }] },
    ],
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.castPlan.baseProjectiles, ['firebolt', 'firebolt', 'firebolt']);
  assert.deepEqual(result.castPlan.onHit, ['spark']);
  assert.equal(result.castPlan.totalManaCost, 55);
});

test('wand compiler rejects recursive trigger loops', () => {
  const loopNode = { kind: 'trigger', id: 'on_hit_cast', payload: [] };
  loopNode.payload.push(loopNode);

  const result = compileWand({ mana: 100, slots: [loopNode] });
  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'TRIGGER_RECURSION');
});

test('route matrix contains six biomes with two side branches each', () => {
  const matrix = buildRouteMatrix();
  assert.equal(matrix.mainline.length, 6);
  for (const biome of matrix.mainline) {
    assert.equal(biome.sideBranches.length, 2);
    assert.equal(typeof biome.hiddenLoop.unlockCondition, 'string');
  }
});

test('material system tick updates reaction queue deterministically', () => {
  const sim = createMaterialSystem({
    width: 3,
    height: 1,
    initial: [
      ['oil', 'fire', 'water'],
    ],
  });

  const report = sim.tick();
  assert.equal(report.reactionsProcessed, 2);
  assert.equal(sim.get(0, 0), 'burning_oil');
  assert.equal(sim.get(2, 0), 'steam');
});

test('reaction table has at least 20 baseline rules', () => {
  const { REACTION_RULES } = require('../src/noita-core.js');
  assert.ok(REACTION_RULES.length >= 20);
});

test('water and lava reaction spawns steam byproduct into adjacent air cell', () => {
  const sim = createMaterialSystem({
    width: 3,
    height: 1,
    initial: [
      ['water', 'lava', 'air'],
    ],
  });

  const report = sim.tick();
  assert.equal(sim.get(0, 0), 'stone');
  assert.equal(sim.get(2, 0), 'steam');
  assert.equal(report.byproductsCreated, 1);
});

test('compileWand rejects expanded cast plan above configured max nodes', () => {
  const result = compileWand(
    {
      mana: 1000,
      slots: [
        { kind: 'base', id: 'firebolt' },
        { kind: 'modifier', id: 'triple_cast' },
      ],
    },
    { maxExpandedNodes: 2 }
  );

  assert.equal(result.ok, false);
  assert.equal(result.error.code, 'CAST_PLAN_TOO_LARGE');
});

test('compileWand returns diagnostics with expandedNodeCount', () => {
  const result = compileWand({
    mana: 1000,
    slots: [
      { kind: 'base', id: 'firebolt' },
      { kind: 'modifier', id: 'triple_cast' },
      { kind: 'trigger', id: 'on_hit_cast', payload: [{ kind: 'base', id: 'spark' }] },
    ],
  });

  assert.equal(result.ok, true);
  assert.ok(result.diagnostics);
  assert.equal(result.diagnostics.expandedNodeCount, 4);
});
