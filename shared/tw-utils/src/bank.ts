// REQ: tw-utils 銀行代碼查詢（3碼 → 銀行名）
// 追溯：twinkle-hub-alignment.md §3、CR-2026-003(ETL)。資料由 ETL 載入 data/bank.json。
import { loadData } from '../etl/load.ts';

const BANK = loadData<Record<string, string>>('bank');

/** 查銀行代碼（3碼）對應銀行名；未命中回 null。 */
export function bankCode(code: string): string | null {
  return BANK[code] ?? null;
}
