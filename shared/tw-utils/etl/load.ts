// ETL:tw-utils:load — 由 data/<name>.json 載入正規化資料（ETL 產出；seed 先行）。
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const DATA_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'data');

export function loadData<T = unknown>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, `${name}.json`), 'utf8')) as T;
}
