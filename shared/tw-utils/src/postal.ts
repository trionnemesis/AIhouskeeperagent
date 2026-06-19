// REQ: tw-utils 郵遞區號查詢（縣市/區 → 3碼）
// 追溯：spec-kit/05-data-mcp/twinkle-hub-alignment.md §3、amenities-mcp.md
// 最小 embedded fixture（範例子集）；完整資料由 ETL（資料層）載入。
// 需正規化 台/臺；未命中回 null。deterministic、無外部依賴。

// Why: 台/臺 為同字異形，key 一律正規化為 '台' 以單一來源比對。
const POSTAL: Record<string, string> = {
  '台北市|信義區': '110',
  '台北市|大安區': '106',
  '高雄市|苓雅區': '802',
};

const normCity = (s: string): string => s.replace(/臺/g, '台');

/** 查 (city, district) 的 3 碼郵遞區號；未命中回 null。 */
export function postalCode(city: string, district: string): string | null {
  return POSTAL[`${normCity(city)}|${district}`] ?? null;
}
