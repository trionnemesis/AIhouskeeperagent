# company-registry-mcp 規格（建商/法人 · P2 部分）

> **本輪僅 spec 可確認部分**（GCIS 公司統編正規化）。建案↔起造人 **blocked-on Q1**；承造人/營造廠(P3) **不做**。決策見 [`decision-matrix.md`](decision-matrix.md) D 區。

## 範圍裁決

| 能力 | 本輪 | 原因 |
|---|---|---|
| GCIS 公司統編正規化 `resolve_company` | ✅ spec | 資料源確認可用（GCIS 公司登記關鍵字查詢 API） |
| 建案 ↔ 起造人 / 建照核發號碼 | ⛔ blocked-on **Q1** | **R2**：起造人不在實登 open data；屬「預售屋建案備查」(dataset 136948)，**開放狀態未確認** |
| 承造人 / 營造廠（建照存根） | ⛔ 不做（P3） | 全國無結構化 open data；含自然人姓名(個資)；爬蟲三重風險（ToS/個資/著作） |

## 1. 資料源（GCIS，verified）

| 項目 | 內容 |
|---|---|
| 來源 | 經濟部 GCIS 公司登記關鍵字查詢 API |
| 介接前置 | 須寄「**使用告知書**」到指定信箱做 **IP 白名單** |
| 限制 | 每日次數上限 + 同時連線上限；分頁 `$skip`/`$top`（≤1000 *unverified，工程介接期驗*） |
| 頻率 | 公司登記每月 10 日 / 稅籍每日（*unverified，待 GCIS OData 官方出處*） |
| 法遵 | 落地散布須在告知書授權目的內（**個資法§20 特定目的外利用**風險，Q6）；DI-8 |

## 2. MCP Tool

```ts
resolve_company(ctx, {
  name?: string,           // 公司名稱關鍵字
  uniform_no?: string,     // 統編
}):
  | { outcome:'provided', matches: Company[], source: '經濟部商業司 GCIS', as_of }
  | { outcome:'refused', reason: 'not_found'|'ambiguous'|'quota_exceeded' }

interface Company {
  uniform_no: string;      // 統編（法人公開，可保留）
  name: string;
  status: string;          // 開放集：核准設立 | 解散 | 撤銷 | …（以 GCIS 實際值為準，不固定 enum）
  // 自然人負責人姓名：DI-1 於 egress 遮罩，不對外明文輸出
}
```

## 3. 正規化規則

- **以統編去重**：同名 / 已解散 / 全形半形 / 繁簡 → 一律以統編為 canonical key。
- 離線字典（twcompany 類）加速容錯比對，降低對 GCIS 的呼叫量（DI-8）。
- **自建 `tw-utils` 統編檢查碼驗證**（重實作 twtools 功能，財政部公開演算法，deterministic）；公司登記查詢走 **GCIS**（非 Twinkle hosted）。**不消費** Twinkle hosted MCP（見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md)）。
- **起造人 ≠ 建商 ≠ 所有權人**（verified，常掛名地主/SPV）→ 即使未來補上起造人資料，仍須交叉統編判讀，**不可直接把起造人映射為建商**。

## 4. 治理對應

| 規則 | 不變量 |
|---|---|
| 自然人姓名於 egress 遮罩；僅落地統編可佐證之法人 | DI-1 |
| 遵 GCIS 每日次數/連線上限；授權目的內使用 | DI-8 |
| 來源顯名（經濟部商業司） | DI-2 |
| provenance 必附 | DI-7 |

## 5. blocked-on Q1（建案↔起造人）

待 open question **Q1** 解（洽內政部地政司：預售屋「建案備查」dataset 136948 是否已開放批次 open data）。若開放：以**建照核發號碼 `case_no`** 為串接鍵，自然人起造人姓名遮罩/不落地，再經本 server 的 `resolve_company` 將建商名→統編正規化。**未解前不寫該 tool spec**，避免以未驗證資料源建構。

## 6. 驗收

見 [`features/company-resolve.feature`](features/company-resolve.feature)。建案↔起造人無 BDD（blocked）。
