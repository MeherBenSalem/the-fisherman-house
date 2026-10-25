#!/usr/bin/env node
'use strict';

const assert = require('assert');
const { detect, detectRequired } = require('./detect-jar-meta.js');

const cases = [
  // 2.0 MultiLoader naming: fisherman_house-{loader}-{minecraft}-{version}.jar
  ['fisherman_house-fabric-1.20.1-2.0.0.jar', 'fabric', '1.20.1'],
  ['fisherman_house-forge-1.20.1-2.0.0.jar', 'forge', '1.20.1'],
  ['fisherman_house-fabric-1.21.1-2.0.0.jar', 'fabric', '1.21.1'],
  ['fisherman_house-neoforge-1.21.1-2.0.0.jar', 'neoforge', '1.21.1'],
  ['fisherman_house-fabric-26.2-2.0.0.jar', 'fabric', '26.2'],
  ['fisherman_house-neoforge-26.2-2.0.0.jar', 'neoforge', '26.2'],
  ['fisherman_house-fabric-26.3-2.0.0.jar', 'fabric', '26.3'],
  ['fisherman_house-neoforge-26.3-2.0.0.jar', 'neoforge', '26.3'],
  ['releases/fisherman_house-neoforge-26.3-2.0.0.jar', 'neoforge', '26.3'],
  // Calendar versions with a patch number must not be read as 1.21.1 or 26.1.
  ['fisherman_house-fabric-26.1.2-2.0.0.jar', 'fabric', '26.1.2'],
  ['fisherman_house-neoforge-26.1.2-2.0.0.jar', 'neoforge', '26.1.2'],
  // 1.1.0 names (same convention), including the dropped 1.21.1 Forge build
  ['fisherman_house-forge-1.21.1-1.1.0.jar', 'forge', '1.21.1'],
  ['fisherman_house-neoforge-26.1.2-1.1.0.jar', 'neoforge', '26.1.2'],
  // Older names with the mod version first
  ['fisherman_house-1.0.0-fabric-1.20.1.jar', 'fabric', '1.20.1'],
];

let failed = 0;
for (const [name, loader, gv] of cases) {
  const got = detect(name);
  try {
    assert.strictEqual(got.loader, loader, `${name} loader`);
    assert.strictEqual(got.gv, gv, `${name} gv`);
    console.log('ok', name, '->', got);
  } catch (e) {
    failed += 1;
    console.error('FAIL', name, 'got', got, e.message);
  }
}

// Unparseable names must fail instead of falling back to a default Minecraft version.
for (const bad of ['fisherman_house-fabric-mystery.jar', 'fisherman_house-fabric-1.20.1-2.0.0-sources.jar']) {
  try {
    detectRequired(bad);
    failed += 1;
    console.error('FAIL expected throw for', bad);
  } catch (e) {
    console.log('ok refuses', bad, ':', e.message.split('\n')[0]);
  }
}

if (failed) {
  console.error(`${failed} case(s) failed`);
  process.exit(1);
}
console.log('all detect-jar-meta cases passed');
