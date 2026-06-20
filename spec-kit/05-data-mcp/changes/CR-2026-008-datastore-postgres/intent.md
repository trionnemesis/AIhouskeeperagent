# Change Intent — CR:2026:008 datastore Postgres 後端

> STDD×VDD Change Package。由 [CR-2026-007](../../../06-platform-gke/changes/CR-2026-007-gke-deployment/gates.md) spawn：GKE 用 Cloud SQL Postgres，data MCP 需多副本 → datastore 由 SQLite 擴為雙後端。

## Change Intent

`packages/datastore` 由純 SQLite 擴充為 **SQLite + PostgreSQL 雙後端**：
- `connect(url)`：`postgresql://...` → psycopg（dict_row）；其餘（路徑/`:memory:`）→ sqlite3（不變）。
- dialect 差異封裝：佔位（`:name` vs `%(name)s`、`?` vs `%s`）、去重（`INSERT OR IGNORE` vs `ON CONFLICT DO NOTHING`）、新增筆數（`total_changes` vs `cursor.rowcount`）、DDL（AUTOINCREMENT vs IDENTITY、REAL vs DOUBLE PRECISION）、`executescript` vs 逐句。
- **函式簽名與 SQLite 行為完全不變**；erd.dbml 本即 PostgreSQL，PG schema 為其落地。

## 為什麼（Driver）

GKE data MCP 為 stateless 多副本（[platform-architecture](../../../06-platform-gke/platform-architecture.md)），SQLite(RWO PVC) 限單副本；Cloud SQL Postgres 解除此限並對齊 erd.dbml。

## 邊界（STDD 硬約束）

- SQLite 路徑零回歸（既有 8 測試 + smoke + e2e 不變）。
- dialect 封裝在 store 內，**呼叫端（server/etl_run/smoke）無感**。
- PG 測試以 `DATABASE_URL` 注入；無則 skip（CI 可選擇起 Postgres service 跑）。
- 新依賴 `psycopg[binary]` 僅 PG 後端需要；純 SQLite/單元測試仍零額外依賴。

## Definition of Ready
- [x] Intent / Delta / Impact / Verification Plan / Acceptance（sqlite 回歸 + 真實 PG + mutation）
