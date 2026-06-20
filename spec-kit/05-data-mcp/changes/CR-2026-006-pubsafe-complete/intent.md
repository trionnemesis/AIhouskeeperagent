# Change Intent — CR:2026:006 public-safety 完整落地 + ETL 韌性

> STDD×VDD Change Package。讓 public-safety 兩工具皆 cache-backed（對稱 lvr），並抽出政府網路共用基建。

## Change Intent

1. **REQ:PUBSAFE:TRAFFIC** — A1/A2 事故點位落地 `traffic_accidents`（erd 既有表）；`traffic_accident_density_tool` 改 cache-backed：讀半徑內點 → 聚合密度。**DI-5**：點位入庫但 tool 僅回密度、不回個別點。
2. **REQ:PUBSAFE:CRIME:BATCH** — `aggregate_crime_all` 全行政區批次；`etl_run crime` 省略 `--region` 即一次落地整份 CSV 所有鄉鎮市區。
3. **REQ:DEPLOY:RETRY** + **重構** — 有界重試 `with_retry`；並將 `build_secure_ssl_context` + `with_retry` 從 `lvr_mcp.ingest` 抽到共用 `packages/govnet`（見「真相」）。

## 已查證真相（2026-06，實測）

- **opdadm.moi.gov.tw（內政部，犯罪/事故源）與 plvr 同樣憑證缺 Subject Key Identifier** → 犯罪 fetcher 也需 `build_secure_ssl_context`。證明此安全修法是**跨來源共用基建**，不可只放 lvr、更不可複製（安全紅線唯一實作）→ 抽 `govnet`。
- 政府 WAF 擋預設 UA（403）→ fetcher 帶瀏覽器 UA。
- 真實 14200 為**逐縣市 CSV**（單檔含多鄉鎮市區）→ 正合「單檔多行政區批次」。

## 邊界（STDD 硬約束）

- 半徑過濾在 **store**（bbox 粗篩 + haversine 精篩）；service 不變（既有 service/guards 測試零破壞）。bbox 經度 delta 用 `cos(lat)` 放寬以保證為超集（不誤刪邊緣點）。
- `parse_accidents_csv` 純函式；A1/A2 由參數帶入（NPA 分檔）；缺/零座標列略過。
- `with_retry` sleeper 注入（deterministic）；**斷路器不在此**（屬 Gateway Router REQ:GW:ROUTER:003）。
- **DI-5**：traffic tool 輸出僅 `aggregate_density`（total_n + severity_mix），無座標。

## Definition of Ready
- [x] Intent / Delta / Impact / Verification Plan / Acceptance（unit + real-run + mutation）
