import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assertScope, scopedWhere, buildSelect } from '../src/index.ts';

// assertScope
test('assertScope: 無 tenantId 拋 SCOPE_UNRESOLVED', () => {
  assert.throws(() => assertScope({}), /SCOPE_UNRESOLVED/);
});

test('assertScope: 有 tenantId/seatId 不拋', () => {
  assert.doesNotThrow(() => assertScope({ tenantId: 't1', seatId: 's1' }));
});

// scopedWhere — Inv-1 自動注入 tenant_id
test('scopedWhere: 注入 tenant_id 並保留 filters', () => {
  assert.deepEqual(
    scopedWhere({ tenantId: 't1', seatId: 's1' }, { district: '信義區' }),
    { district: '信義區', tenant_id: 't1' },
  );
});

test('scopedWhere: filters 帶異租戶 tenant_id 拋 SCOPE_VIOLATION', () => {
  assert.throws(
    () => scopedWhere({ tenantId: 't1' }, { tenant_id: 't2' }),
    /SCOPE_VIOLATION/,
  );
});

test('scopedWhere: 無 ctx 拋 SCOPE_UNRESOLVED', () => {
  assert.throws(() => scopedWhere(undefined, {}), /SCOPE_UNRESOLVED/);
});

// 獨立 pin 同租戶放行分支（Verify agent 找到的覆蓋缺口）
test('scopedWhere: filters 帶同租戶 tenant_id 放行', () => {
  assert.deepEqual(
    scopedWhere({ tenantId: 't1', seatId: 's1' }, { tenant_id: 't1', district: '信義區' }),
    { tenant_id: 't1', district: '信義區' },
  );
});

// buildSelect
test('buildSelect: 組出 table + scoped where', () => {
  assert.deepEqual(
    buildSelect({ tenantId: 't1', seatId: 's1' }, 'customers', {}),
    { table: 'customers', where: { tenant_id: 't1' } },
  );
});
