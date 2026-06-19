// ETL:tw-utils:sources — 官方來源描述（顯名 DI-2 / license DI-8）。實際下載為 deploy-time。
import type { SourceDesc } from './run.ts';

export type SourceManifest = SourceDesc & { source: string; license: string };

export const SOURCES: SourceManifest[] = [
  { name: 'postal',  sourceId: 'cht-post-zip', kind: 'postal',  source: '中華郵政 3+2 郵遞區號 (data.gov.tw)', license: '政府資料開放授權第1版' },
  { name: 'city-en', sourceId: 'moi-admin-en', kind: 'city-en', source: '內政部 縣市行政區英譯',              license: '政府資料開放授權第1版' },
  { name: 'metro',   sourceId: 'tdx-metro',    kind: 'metro',   source: 'TDX 運輸資料流通服務',                license: 'TDX 服務條款' },
  { name: 'bank',    sourceId: 'fisc-bank',    kind: 'bank',    source: '財金公司/data.gov.tw 金融機構代號',   license: '政府資料開放授權第1版' },
];
