import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runEtl, type Fetcher, type SourceDesc } from '../etl/run.ts';
import { SOURCES } from '../etl/sources.ts';

test('每個來源標 source + license（DI-2 顯名 / DI-8 授權）', () => {
  assert.ok(SOURCES.length >= 4);
  for (const s of SOURCES) {
    assert.ok(s.source && s.source.length > 0, `${s.name} 缺 source`);
    assert.ok(s.license && s.license.length > 0, `${s.name} 缺 license`);
  }
});

test('runEtl: 用注入 fetcher（DI），不真實下載', async () => {
  const fake: Fetcher = async (id) =>
    (({
      postal: [{ city: '台北市', district: '信義區', zip: '110' }],
      bank: [{ code: '004', name: '臺灣銀行' }],
    }) as Record<string, Record<string, string>[]>)[id] ?? [];

  const sources: SourceDesc[] = [
    { name: 'postal', sourceId: 'postal', kind: 'postal' },
    { name: 'bank', sourceId: 'bank', kind: 'bank' },
  ];
  const out = await runEtl(fake, sources);
  assert.deepEqual(out.postal, { '台北市|信義區': '110' });
  assert.deepEqual(out.bank, { '004': '臺灣銀行' });
});
