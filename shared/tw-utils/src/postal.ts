// REQ: tw-utils 郵遞區號查詢（縣市/區 → 3碼）
// 追溯：twinkle-hub-alignment.md §3、amenities-mcp.md、CR-2026-003(ETL)
// 資料由 ETL 載入 data/postal.json（seed 先行，完整資料由 ETL 對中華郵政產出）。

import { loadData } from '../etl/load.ts';

const POSTAL = loadData<Record<string, string>>('postal');
// Why: 台/臺 同字異形，查詢值正規化為 '台'（data key 已正規化）。
const normCity = (s: string): string => s.replace(/臺/g, '台');

/** 查 (city, district) 的 3 碼郵遞區號；未命中回 null。 */
export function postalCode(city: string, district: string): string | null {
  return POSTAL[`${normCity(city)}|${district}`] ?? null;
}
