# lvr-mcp 規格（實價登錄 · P0）

> 行情底座與查價主流程。Python FastMCP，streamable-http 獨立進程。資料 = 內政部官方 plvr ZIP（法遵🟢，授權第1版，免費商用）。

## 1. 資料源（verified）

| 項目 | 內容 |
|---|---|
| 來源 | 內政部不動產交易實價查詢服務網（plvr）批次下載 |
| 本期下載 | `/Download`（最新一期 ZIP） |
| 歷史下載 | `/DownloadSeason`（逐季迴圈回補） |
| 對照 dataset | data.gov.tw **25119 / 77051**（買賣）；**139728**（預售屋去識別逐筆，含建案名欄位 `rps28`）；預售 ZIP `lvr_landBcsv.zip` |
| 格式 | CSV（big5/UTF-8 視檔），分檔：main(主檔)、build(建物)、land(土地)、park(車位) |
| 發布頻率 | 每月 **1 / 11 / 21**；揭露約 **45 天前**登錄之交易 |
| 授權 | 政府資料開放授權第1版（≈CC-BY，**須顯名**，得商用，免費不限流量） |

> ⚠️ **R1（PII）**：自 2021/7 實價登錄 2.0 起**門牌/地號完整揭露、來源未脫敏** → PII 遮罩責任全在 Gateway（DI-1），lvr-mcp **不得**假設來源已去識別。

## 2. Ingest pipeline

```
plvr ZIP (/Download + /DownloadSeason 回補)
  → 解壓 + 編碼正規化
  → JOIN main + build + land + park (以交易序號)
  → 重算每坪「淨」單價：(總價 − 車位價) / (主+附屬建物坪數)   # 不可直接用來源單價欄
  → 備註欄解析特殊交易旗標：親友交易/含裝潢/含車位/債權債務/急售/分管…
  → TimestampGuard：剔除 trade_date 異常（沿用主 spec Inv-4：<2010 或 >今日+90天）
  → 標 data_as_of + 申報遲延警示（DI-3/DI-9）
  → 寫入 lvr cache（短 TTL；近 1-2 季定期重抓校正 DI-9）
```

**為什麼重算單價**：來源單價欄含車位灌水/坪數口徑不一，直接用會報錯價（延續主 spec 錯價零容忍）。

## 3. MCP Tools

```ts
// 成交行情查詢 【P0】
query_market(ctx, {
  district: string,            // 行政區（受控詞彙）
  deal_type: 'sale'|'rent',
  building_type?: '預售'|'成屋'|'中古',
  date_range?: { from: 'YYYY-MM', to: 'YYYY-MM' },
  room_layout?: string,
}):
  | { outcome: 'provided', comps: Comp[], stats: { median_unit_price, n },
      data_as_of: string, source: '內政部不動產交易實價查詢服務網',
      disclaimer: string, lag_warning?: string }      // DI-2/DI-3
  | { outcome: 'refused', reason: 'stale'|'garbage'|'low_confidence'|'addr_mismatch'|'insufficient_comps'|'source_unavailable' }
// 防護：TimestampGuard(Inv-4) + 重算單價 + 拒答優於猜測(Inv-5)；reason 全為純領域 refused，
//      其中 source_unavailable 內部對映 MARKET_SOURCE_UNAVAILABLE(REL-4)，見 ../02-spec/error-model.md

// 預售屋成交 + 建案名 【P1】
query_presale(ctx, {
  district: string, project_name?: string, date_range?: {...}
}): { outcome, presales: Presale[] /* 含 project_name(rps28), 但無起造人/建商 */, data_as_of, source }
// ⚠️ 起造人/建商不在此資料（R2）→ 見 company-registry-mcp 缺口

// 註：單一地址周邊 comps（nearby_comps）為 P2 候選，未於本輪決策矩陣拍板，暫不規格化。

interface Comp {
  trade_date: string; district: string; building_type: string;
  total_price: number; unit_price_net: number;   // 重算後淨單價
  area_ping: number; room_layout?: string;
  flags: string[];          // 特殊交易旗標
  has_parking: boolean; parking_price?: number;
}
```

## 4. 防護鏈（延續主 spec C8 + DI 系列）

| 防護 | 規則 | 不變量 |
|---|---|---|
| 日期防呆 | 剔除 trade_date <2010 或 >今日+90天（濾 2101/1921 垃圾值） | Inv-4 |
| 拒答優於猜測 | 地址比對失敗 / comps 不足 / 信心低 → `refused` | Inv-5 |
| 標註義務 | 必附 data_as_of + 預售/成屋/車位標註 + 申報遲延警示 + 來源顯名 | Inv-6/DI-2/DI-3 |
| 快取時效 | 短 TTL；近 1-2 季定期重抓校正 | DI-9 |
| PII | 門牌/地號於 Gateway egress 遮罩（不在本 server 假設已脫敏） | DI-1 |

## 5. 錯誤碼（見 [`../02-spec/error-model.md`](../02-spec/error-model.md)）

`MARKET_SOURCE_UNAVAILABLE`(plvr 下載失敗→降級拒答 REL-4)、其餘 refused 為純領域 reason（非 DomainError）。

## 6. 與 Twinkle Hub Real-estate(LVR) 的關係

**不消費** Twinkle hosted LVR MCP（Q8/Q10 已拍板自建）。**權威源 = 自建 ingest（本 server，官方 plvr）**；介面切分（sales/rentals/pre-sale）可參考其設計，但**無 Twinkle 執行期依賴、無 fallback**；交叉比對僅用歷史官方資料。詳見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md)。

## 7. 驗收

見 [`features/lvr-market.feature`](features/lvr-market.feature)；門牌/地號 PII 驗收見 [`features/gateway-pii-egress.feature`](features/gateway-pii-egress.feature)（DI-1 屬 Gateway 層）。
