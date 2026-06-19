// REQ: tw-utils 銀行代碼查詢（3碼 → 銀行名）
// 追溯：spec-kit/05-data-mcp/twinkle-hub-alignment.md §3、amenities-mcp.md
// 最小 embedded fixture（範例子集）；完整資料由 ETL（資料層）載入。
// 未命中回 null。deterministic、無外部依賴。

const BANK: Record<string, string> = {
  '004': '臺灣銀行',
  '822': '中國信託商業銀行',
  '700': '中華郵政',
};

/** 查銀行代碼（3碼）對應銀行名；未命中回 null。 */
export function bankCode(code: string): string | null {
  return BANK[code] ?? null;
}
