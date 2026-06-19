// REQ: tw-utils 捷運路線查詢（系統/站名 → 路線清單）
// 追溯：spec-kit/05-data-mcp/twinkle-hub-alignment.md §3、amenities-mcp.md
// 最小 embedded fixture（範例子集）；完整資料由 ETL（資料層）載入。
// 未命中回 null（轉乘站回多條路線）。deterministic、無外部依賴。

const METRO: Record<string, Record<string, string[]>> = {
  '台北捷運': {
    '市政府': ['板南線'],
    '台北車站': ['板南線', '淡水信義線'],
  },
};

/** 查 (system, station) 的路線清單；未命中回 null。 */
export function metroLine(system: string, station: string): string[] | null {
  return METRO[system]?.[station] ?? null;
}
