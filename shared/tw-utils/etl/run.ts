// ETL:tw-utils:run — DI'd runner。fetcher 注入（個人偏好 DI > 直接實例化）；
// 實際下載（中華郵政/TDX/財金）為 deploy-time I/O，由注入的 fetcher 提供。
import { transformPostal, transformBank, transformCityEn, transformMetro, type RawRow } from './transform.ts';

const TRANSFORMS = {
  postal: transformPostal,
  bank: transformBank,
  'city-en': transformCityEn,
  metro: transformMetro,
} as const;

export type Fetcher = (sourceId: string) => Promise<RawRow[]>;
export type SourceDesc = { name: string; sourceId: string; kind: keyof typeof TRANSFORMS };

/** 對每個來源：fetch(raw) → transform → 收集為 { name: normalized }。 */
export async function runEtl(fetcher: Fetcher, sources: SourceDesc[]): Promise<Record<string, unknown>> {
  const out: Record<string, unknown> = {};
  for (const s of sources) {
    const raw = await fetcher(s.sourceId);
    out[s.name] = (TRANSFORMS[s.kind] as (rows: RawRow[]) => unknown)(raw);
  }
  return out;
}
