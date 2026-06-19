// REQ: tw-utils 民國↔西元 / 民國季解析
// 追溯：spec-kit/05-data-mcp/lvr-mcp.md（data_as_of、民國季 115S1=2026Q1、TimestampGuard 脈絡）
// deterministic、無外部依賴。

/** 民國年 → 西元年（+1911）。 */
export function rocYearToGregorian(rocYear: number): number {
  return rocYear + 1911;
}

/**
 * 解析民國季字串（如 "115S1"）→ { gregorianYear, quarter }。
 * 格式不符或季別超出 1–4 回 null。
 */
export function parseRocSeason(s: string): { gregorianYear: number; quarter: number } | null {
  const m = /^(\d+)S([1-4])$/.exec(s);
  if (!m) return null;
  return { gregorianYear: rocYearToGregorian(Number(m[1])), quarter: Number(m[2]) };
}
