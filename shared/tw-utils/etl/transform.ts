// ETL:tw-utils:transform — 純 transform（raw open-data row → normalized）。deterministic、無 I/O。
// 追溯：spec-kit/05-data-mcp/changes/CR-2026-003-tw-utils-etl/

export type RawRow = Record<string, string>;

// Why: 台/臺 同字異形，key 一律正規化為 '台'（單一比對來源）。
const normCity = (s: string): string => s.replace(/臺/g, '台');

/** 郵遞區號：{city, district, zip} → { "台北市|信義區": "110" } */
export function transformPostal(rows: RawRow[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const r of rows) out[`${normCity(r.city)}|${r.district}`] = r.zip;
  return out;
}

/** 銀行代碼：{code, name} → { "004": "臺灣銀行" } */
export function transformBank(rows: RawRow[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const r of rows) out[r.code] = r.name;
  return out;
}

/** 縣市英譯：{zh, en} → { "台北市": "Taipei City" }（zh 正規化） */
export function transformCityEn(rows: RawRow[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const r of rows) out[normCity(r.zh)] = r.en;
  return out;
}

/** 捷運：{system, station, line} → { system: { station: [lines...] } }（累積多線） */
export function transformMetro(rows: RawRow[]): Record<string, Record<string, string[]>> {
  const out: Record<string, Record<string, string[]>> = {};
  for (const r of rows) {
    (out[r.system] ??= {});
    (out[r.system][r.station] ??= []).push(r.line);
  }
  return out;
}
