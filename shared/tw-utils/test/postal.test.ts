// GATE:RED → GATE:GREEN 驗收：郵遞區號查詢。
// 測試向量為題目給定（手算/查表，非複製 production 演算法到測試，治理頁06）。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { postalCode } from '../src/postal.ts';

test('postalCode: 命中（含 台/臺 正規化）', () => {
  assert.equal(postalCode('台北市', '信義區'), '110');
  assert.equal(postalCode('臺北市', '大安區'), '106'); // 臺 與 台 視為同一
  assert.equal(postalCode('高雄市', '苓雅區'), '802');
});

test('postalCode: 未命中回 null', () => {
  assert.equal(postalCode('火星', 'X'), null);
});
