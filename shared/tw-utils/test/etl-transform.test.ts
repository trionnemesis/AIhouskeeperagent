import { test } from 'node:test';
import assert from 'node:assert/strict';
import { transformPostal, transformBank, transformCityEn, transformMetro } from '../etl/transform.ts';

test('transformPostal: 正規化 臺→台，建 city|district→zip', () => {
  assert.deepEqual(
    transformPostal([
      { city: '臺北市', district: '信義區', zip: '110' },
      { city: '高雄市', district: '苓雅區', zip: '802' },
    ]),
    { '台北市|信義區': '110', '高雄市|苓雅區': '802' },
  );
});

test('transformBank: code→name', () => {
  assert.deepEqual(transformBank([{ code: '004', name: '臺灣銀行' }]), { '004': '臺灣銀行' });
});

test('transformCityEn: 正規化 zh→en', () => {
  assert.deepEqual(transformCityEn([{ zh: '臺北市', en: 'Taipei City' }]), { '台北市': 'Taipei City' });
});

test('transformMetro: 累積站的多條路線', () => {
  assert.deepEqual(
    transformMetro([
      { system: '台北捷運', station: '台北車站', line: '板南線' },
      { system: '台北捷運', station: '台北車站', line: '淡水信義線' },
      { system: '台北捷運', station: '市政府', line: '板南線' },
    ]),
    { '台北捷運': { '台北車站': ['板南線', '淡水信義線'], '市政府': ['板南線'] } },
  );
});
