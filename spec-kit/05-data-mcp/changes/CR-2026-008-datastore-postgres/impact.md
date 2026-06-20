# Impact Analysis — CR:2026:008 datastore Postgres 後端

| 元件 | 變更 | 風險 | 緩解 |
|---|---|---|---|
| `datastore/store.py` | 雙後端 dialect 封裝 | SQLite 行為漂移 | 既有 8 測試 + smoke + e2e 全綠（零回歸） |
| PG 去重 | `ON CONFLICT DO NOTHING` | 漏寫→UNIQUE 爆 IntegrityError | 真實 PG 測試 + mutation 驗證 |
| 連線 | psycopg dict_row | row 存取差異 | `dict(r)` 對兩後端皆可；查詢回傳一致 |
| 依賴 | psycopg[binary] | 體積/平台 | 僅 PG 後端載入（lazy import）；SQLite 路徑零依賴 |

## 不變量
- **DI-5**：crime_area_stats 兩後端皆無 lat/lng 欄（PG 以 information_schema 驗）。
- **DI-7**：provenance 跨後端一致落地。
- 去重鍵與語意跨後端一致（lvr/crime/traffic）。

## 回滾
- revert 本 CR → 回純 SQLite；server/etl_run 介面不變，無連動。

## 部署相依
- 與 [CR-2026-007](../../../06-platform-gke/changes/CR-2026-007-gke-deployment/gates.md) 一起執行：Cloud SQL 起 + `DATA_MCP_DB=postgresql://...` 注入後，data MCP 即多副本。
