// GATE:RED → GATE:GREEN 驗收：銀行代碼查詢。
// 測試向量為題目給定（非複製 production 演算法到測試，治理頁06）。
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bankCode } from '../src/bank.ts';

test('bankCode: 命中', () => {
  assert.equal(bankCode('004'), '臺灣銀行');
  assert.equal(bankCode('822'), '中國信託商業銀行');
  assert.equal(bankCode('700'), '中華郵政');
});

test('bankCode: 未命中回 null', () => {
  assert.equal(bankCode('999'), null);
});
