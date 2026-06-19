// GATE:RED → GATE:GREEN 驗收：地址工具（縣市英譯、後綴縮寫）。
// 測試向量為題目給定（非複製 production 演算法到測試，治理頁06）。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cityToEnglish, normalizeAddressSuffix } from '../src/address.ts';

test('cityToEnglish: 直轄市命中', () => {
  assert.equal(cityToEnglish('台北市'), 'Taipei City');
  assert.equal(cityToEnglish('新北市'), 'New Taipei City');
  assert.equal(cityToEnglish('高雄市'), 'Kaohsiung City');
});

test('cityToEnglish: 未命中回 null', () => {
  assert.equal(cityToEnglish('火星'), null);
});

test('normalizeAddressSuffix: 中→英縮寫', () => {
  assert.equal(normalizeAddressSuffix('路'), 'Rd.');
  assert.equal(normalizeAddressSuffix('街'), 'St.');
  assert.equal(normalizeAddressSuffix('段'), 'Sec.');
  assert.equal(normalizeAddressSuffix('號'), 'No.');
  assert.equal(normalizeAddressSuffix('巷'), 'Ln.');
  assert.equal(normalizeAddressSuffix('弄'), 'Aly.');
});

test('normalizeAddressSuffix: 未知回 null', () => {
  assert.equal(normalizeAddressSuffix('村'), null);
});
