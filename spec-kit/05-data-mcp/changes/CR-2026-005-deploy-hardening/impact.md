# Impact Analysis — CR:2026:005 部署硬化

## 觸及範圍

| 元件 | 變更 | 風險 | 緩解 |
|---|---|---|---|
| `lvr_mcp/ingest.py` | 加 `build_secure_ssl_context`；`live_fetch_plvr` 改用 | 安全：誤關驗證 | 純函式測試斷言 `CERT_REQUIRED`+`check_hostname`；mutation 證紅 |
| `lvr_mcp/schedule.py` | 新模組（純） | 邊界（旬/月/年交界、發布日當天） | 4 邊界測試（含跨年）；`>=` 變異被殺 |
| `datastore/` | 新 package（SQLite 落地 erd） | 去重失效、provenance 漏記、洩座標 | dedup/provenance/無座標欄測試；2 變異被殺 |
| `lvr_mcp/server.py` | `query_market_tool` cache-backed（**簽名變更**） | breaking：呼叫端 | 見 delta.migration；smoke 覆蓋無快取→refused |
| `public_safety_mcp/server.py` | `area_crime_stats_tool` cache-backed + `mcp.run()`（**簽名變更**） | breaking + 粒度 | 門牌 scope→refused 仍先於讀快取（DI-5） |
| `scripts/etl_run.py`/`serve.py` | 新 I/O 入口 | — | 真實 e2e 驗證 |
| `scripts/deploy_smoke.py` | 改 seed→cache-backed | — | GATE:DEPLOY 實跑 |

## 不變量交互

- **TLS-1（新，安全紅線）**：`build_secure_ssl_context()` 回傳的 context 恆 `verify_mode==CERT_REQUIRED` 且 `check_hostname==True`；僅 `VERIFY_X509_STRICT` 被清。
- **Inv-5**：cache 空或 guarded < min_comps → `refused`（無快取行政區實測 refused）。
- **DI-5**：`crime_area_stats` 無座標欄；`area_crime_stats_tool` 對門牌/地號 scope 先 `refused` 再不讀快取。
- **DI-7**：每批 upsert 寫 provenance（authority=gov）。
- **DI-9**：`etl_run lvr` 預設抓「本季+上季」；`is_stale` 供新鮮度告警。

## 真實資料佐證（e2e）

- plvr 115S1 台北市：安全 context **下載成功（無 SSL 錯）** → 解析 5366 → 去重落地 5266 → 信義區 365；erd 衍生欄 `area_ping`/`unit_price_net` 重算；provenance gov 記錄；server cache 查詢回 `provided n=365`。

## 回滾

- 純新增 + 簽名變更集中在 2 個 server tool；回滾 = revert 本 CR commit，呼叫端回 CR-2026-004 的 args 形態。
