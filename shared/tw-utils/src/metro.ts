// REQ: tw-utils 捷運路線查詢（系統/站名 → 路線清單）
// 追溯：twinkle-hub-alignment.md §3、amenities-mcp.md、CR-2026-003(ETL)。資料由 ETL 載入 data/metro.json。
import { loadData } from '../etl/load.ts';

const METRO = loadData<Record<string, Record<string, string[]>>>('metro');

/** 查 (system, station) 的路線清單；未命中回 null（轉乘站回多條路線）。 */
export function metroLine(system: string, station: string): string[] | null {
  return METRO[system]?.[station] ?? null;
}
