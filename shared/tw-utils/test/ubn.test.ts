// GATE:RED → GATE:GREEN 驗收：統編檢查碼。
// 測試向量為手算（非複製 production 演算法到測試，防自證式測試，治理頁06）。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateUbn } from '../src/ubn.ts';

// 一般情形（第7碼非7，總和digitsum%5==0）
test('valid UBN, no special case (12345601 → 25%5==0)', () => {
  assert.equal(validateUbn('12345601'), true);
});

// 第7碼為7的特例（總和+1 後 %5==0）
test('valid UBN, 7th-digit-7 special case (12345675 → 39, +1=40)', () => {
  assert.equal(validateUbn('12345675'), true);
});

// 檢查碼錯誤
test('invalid checksum (12345602 → 26%5!=0)', () => {
  assert.equal(validateUbn('12345602'), false);
});

// 格式：非 8 位 / 非數字
test('rejects malformed input', () => {
  assert.equal(validateUbn('1234567'), false);   // 7 碼
  assert.equal(validateUbn('123456012'), false);  // 9 碼
  assert.equal(validateUbn('1234560a'), false);   // 非數字
  assert.equal(validateUbn(''), false);
});
