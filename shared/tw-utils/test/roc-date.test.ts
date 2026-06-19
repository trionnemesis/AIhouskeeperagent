import { test } from 'node:test';
import assert from 'node:assert/strict';
import { rocYearToGregorian, parseRocSeason } from '../src/roc-date.ts';

test('rocYearToGregorian: +1911', () => {
  assert.equal(rocYearToGregorian(115), 2026);
  assert.equal(rocYearToGregorian(114), 2025);
  assert.equal(rocYearToGregorian(1), 1912);
});

test('parseRocSeason: 115S1 → 2026 Q1（報告實測錨點）', () => {
  assert.deepEqual(parseRocSeason('115S1'), { gregorianYear: 2026, quarter: 1 });
  assert.deepEqual(parseRocSeason('114S4'), { gregorianYear: 2025, quarter: 4 });
});

test('parseRocSeason: 格式/範圍錯誤回 null', () => {
  assert.equal(parseRocSeason('115S5'), null); // 季超範圍
  assert.equal(parseRocSeason('115S0'), null);
  assert.equal(parseRocSeason('115'), null);   // 無季
  assert.equal(parseRocSeason('abcS1'), null); // 非數字年
  assert.equal(parseRocSeason(''), null);
});
