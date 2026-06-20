# Change Intent — CR:2026:005 部署硬化（TLS / 排程 / 快取落地）

> STDD×VDD Change Package。收尾 [CR-2026-004](../CR-2026-004-real-ingest/gates.md) 的 `GATE:DEPLOY ⏳` 三項，讓 MCP server 進入「真正部署」形態。

## Change Intent

三組需求（皆 deploy-time）：

1. **REQ:DEPLOY:TLS** — plvr live fetch 的安全 TLS 修正。
2. **REQ:DEPLOY:SCHED** — plvr 每旬發布（1/11/21）排程 + 新鮮度監控（DI-9）。
3. **REQ:DEPLOY:STORE** — ingest 結果落地 erd.dbml 快取表；server 改 cache-backed；補 `mcp.run()` 部署入口。

## 已查證真相（2026-06，實測 ground truth）

- **TLS**：`plvr.land.moi.gov.tw` 憑證鏈缺 **Subject Key Identifier**（RFC5280 結構不符）。Python 3.14 / OpenSSL 3.6 **預設開啟** `VERIFY_X509_STRICT` 故拒。實測 **certifi/補 CA 皆無效**（非信任根缺失）。唯一安全修法：**僅清 `VERIFY_X509_STRICT`**，`CERT_REQUIRED` + `check_hostname` 全保留；反向控制（換錯 hostname）仍被拒 → 密碼學驗證完整。
- **排程**：plvr 實價登錄每月 **1/11/21** 發布（每旬），季別字串 `民國年S季`（如 `115S2`）。申報遲延 3–5 月 → ETL 同抓「本季+上季」校正（DI-9）。
- **落地**：erd.dbml 為單一 `lvr_data_mcp` schema → 以**單一 SQLite db** 落地已 ingest 的表（`lvr_trades` / `crime_area_stats` / `provenance`）。

## 邊界（STDD 硬約束）

- 安全核心是**純函式** `build_secure_ssl_context()`（驗證旗標可測），下載為 I/O。
- 排程是**純函式** `next_publication_date` / `is_stale` / `season_for`（時間以參數注入），cron 觸發與 I/O 在 `scripts/etl_run.py`。
- store 為 **domain-agnostic 持久層**（連線 per-call、`ingested_at` 以 DI 注入）；欄位映射由各 MCP 的 ETL runner 負責，避免 store→domain 依賴循環。
- **DI-5**：`crime_area_stats` schema **刻意無 `lat`/`lng` 欄**（區域級封頂即護欄）。
- **DI-7**：每批 upsert 記 provenance（source/authority/confidence/as_of）。
- **禁止** 任何 `CERT_NONE` / `check_hostname=False`（安全紅線）。

## Definition of Ready
- [x] Intent / Delta / Impact / Verification Plan / Acceptance（unit + real-run + mutation）
