# Impact Analysis — CR:2026:006 public-safety 完整落地

## 觸及範圍

| 元件 | 變更 | 風險 | 緩解 |
|---|---|---|---|
| `packages/govnet/`（新） | TLS/retry 共用基建 | 安全紅線唯一實作 | govnet/tests：CERT_REQUIRED+check_hostname、retry backoff；M8 變異被殺 |
| `lvr_mcp/ingest.py` | 改 import govnet（移除本地 TLS/retry） | 回歸 | lvr 19 測試綠（TLS/retry 案例移 govnet） |
| `public_safety_mcp/ingest.py` | `aggregate_crime_all`、`parse_accidents_csv`、`live_fetch_crime` 改 govnet+UA+retry | opdadm 缺 SKI | 真實 14200 e2e 成功（fetcher 修好） |
| `datastore/store.py` | traffic_accidents 表 + bbox+haversine 半徑查詢 | 邊緣點誤刪 | bbox 經度 cos(lat) 放寬為超集；角點測試 + M5 變異被殺 |
| `public_safety_mcp/server.py` | traffic tool cache-backed（**簽名變更**） | breaking | 見 migration；smoke 半徑 2/3 點、無座標 |
| `scripts/etl_run.py` | crime 全行政區批次 + traffic 子命令 | — | 真實批次 e2e |

## 不變量交互

- **DI-5**：`traffic_accidents` 存點位（聚合所需），但 `query_accident_points_near` 為**內部**，tool 僅輸出 `aggregate_density`（total_n+severity_mix，無座標）。crime 維持鄉鎮市區。
- **TLS-1**：govnet context 仍 `CERT_REQUIRED`+`check_hostname`；僅清 `VERIFY_X509_STRICT`。
- **DI-7**：traffic/crime 每批落地記 provenance（gov）。
- **Inv-4**：事故 `occurred_at` 由 ROC→ISO（缺/壞日期可被 guard 過濾）。

## 真實資料佐證（e2e）

- **犯罪全行政區批次**：真實 14200（opdadm，安全 context+UA fetcher）→ **340 groups / 1107 stat 列 / 329 行政區**；DI-5 無座標欄；top：桃園區 毒品 355（真實）；server `area_crime_stats_tool(七堵區)`→provided/鄉鎮市區/4 stats。
- **traffic**：邏輯 unit+smoke 全證（半徑 2/3 點、DI-5 無座標）；共用 fetcher 已由犯罪真實驗證（同 opdadm 主機）；A1/A2 dataset URL 為 operator 設定（I/O 邊界）。

## 回滾

- revert 本 CR；traffic tool 回 args 形態、TLS/retry 回 lvr_mcp.ingest。
