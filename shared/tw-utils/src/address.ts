// REQ: tw-utils 地址工具（縣市英譯、地址後綴中→英縮寫）
// 追溯：spec-kit/05-data-mcp/twinkle-hub-alignment.md §3、amenities-mcp.md
// 最小 embedded fixture（範例子集）；完整資料由 ETL（資料層）載入。
// 未命中回 null。deterministic、無外部依賴。

// Why: 台/臺 同字異形，key 正規化為 '台'。
const CITY_EN: Record<string, string> = {
  '台北市': 'Taipei City',
  '新北市': 'New Taipei City',
  '高雄市': 'Kaohsiung City',
};

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
