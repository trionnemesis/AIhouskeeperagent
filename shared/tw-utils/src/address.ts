// REQ: tw-utils 地址工具（縣市英譯、地址後綴中→英縮寫）
// 追溯：twinkle-hub-alignment.md §3、amenities-mcp.md、CR-2026-003(ETL)
// 縣市英譯由 ETL 載入 data/city-en.json；後綴為規則（embedded）。

import { loadData } from '../etl/load.ts';

const CITY_EN = loadData<Record<string, string>>('city-en');

// 地址後綴為規則對應（非資料集），維持 embedded。
const SUFFIX_EN: Record<string, string> = {
  '路': 'Rd.',
  '街': 'St.',
  '段': 'Sec.',
  '號': 'No.',
  '巷': 'Ln.',
  '弄': 'Aly.',
};

/** 直轄市中文 → 英譯（如 '台北市'→'Taipei City'）；未命中回 null。 */
export function cityToEnglish(city: string): string | null {
  return CITY_EN[city.replace(/臺/g, '台')] ?? null;
}

/** 地址後綴 token 中→英縮寫（如 '路'→'Rd.'）；未知回 null。 */
export function normalizeAddressSuffix(token: string): string | null {
  return SUFFIX_EN[token] ?? null;
}
