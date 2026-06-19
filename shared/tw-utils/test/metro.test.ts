// GATE:RED → GATE:GREEN 驗收：捷運路線查詢。
// 測試向量為題目給定（非複製 production 演算法到測試，治理頁06）。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { metroLine } from '../src/metro.ts';

test('metroLine: 單線站', () => {
  assert.deepEqual(metroLine('台北捷運', '市政府'), ['板南線']);
});

test('metroLine: 轉乘站含多條路線', () => {
  const lines = metroLine('台北捷運', '台北車站');
  assert.ok(Array.isArray(lines), '應回陣列');
  assert.ok(lines!.includes('板南線'), '應含板南線');
  assert.ok(lines!.includes('淡水信義線'), '應含淡水信義線');
});

test('metroLine: 未命中回 null', () => {
  assert.equal(metroLine('台北捷運', '火星'), null);
});
