const test = require('node:test');
const assert = require('node:assert/strict');

const {
  buildTotemArtManifest,
  buildTotemSvg,
} = require('../src/noita-art.js');

test('buildTotemSvg returns svg data uri', () => {
  const uri = buildTotemSvg({
    key: 'warrior',
    title: '战士',
    accent: '#d8b36a',
    eye: '#fff2b0',
    sigil: 'shield',
  });

  assert.match(uri, /^data:image\/svg\+xml;charset=UTF-8,/);
  assert.match(decodeURIComponent(uri), /<svg/);
  assert.match(decodeURIComponent(uri), /战士/);
});

test('buildTotemArtManifest includes hero enemy and boss collections', () => {
  const manifest = buildTotemArtManifest();
  assert.ok(manifest.classPortraits.warrior);
  assert.ok(manifest.enemies.skeleton.src);
  assert.ok(manifest.bosses.boss_lord.src);
});

test('boss manifest includes flavor tip and generated svg', () => {
  const manifest = buildTotemArtManifest();
  assert.match(manifest.bosses.boss_dragon.tip, /骨龙|召唤/);
  assert.match(manifest.bosses.boss_dragon.src, /^data:image\/svg\+xml/);
});

test('enemy manifest keeps cute abstract rune-totem notes', () => {
  const manifest = buildTotemArtManifest();
  assert.match(manifest.enemies.cultist.note, /图腾|符文|袍/);
  assert.match(decodeURIComponent(manifest.enemies.cultist.src), /mask/);
});
