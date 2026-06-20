# Gate Checklist — CR:2026:006 public-safety 完整落地

## GATE:SPEC ✅
- [x] Intent/Delta/Impact/Verification；Stable ID（PUBSAFE:TRAFFIC/CRIME、GOVNET、DEPLOY:RUN:traffic）；breaking=true + migration；refactor 記錄

## GATE:RED ✅（實跑）
- [x] datastore traffic（3 errors）、ps ingest accidents+all（ImportError）、lvr retry（ImportError）

## GATE:GREEN ✅（實跑）
- [x] 新測：datastore traffic 3、ps ingest 4（all 2 + accidents 2）、govnet 5（TLS 2 + retry 3）
- [x] 回歸全綠：govnet 5 / lvr 19 / public-safety 23 / datastore 8 / scope-helper 7 / tw-utils 24

## GATE:VDD ✅（實跑，cp+diff+清 pycache）
- [x] M5 haversine 精篩失效 → 殺 traffic 半徑測試（角點守護）
- [x] M6 aggregate_crime_all 只按 county → 殺全行政區測試
- [x] M7 parse_accidents 不跳缺座標 → 殺 parse 測試（failures=2）
- [x] M8 with_retry 不重試 → 殺 retry 測試
- [x] 四者還原後復綠

## GATE:DEPLOY ✅（實跑）
- [x] **真實犯罪全行政區批次**：14200（opdadm 安全 context+UA）→ 340 groups / 1107 列 / **329 行政區**；DI-5 無座標；server `area_crime_stats_tool(七堵區)`→provided
- [x] **gov fetcher 安全**：opdadm.moi.gov.tw 下載成功（govnet context；先前 SKI 失敗已修）
- [x] **smoke**：traffic cache-backed 半徑內 2/3 點聚合、DI-5 無座標
- [x] traffic 邏輯 unit+smoke 全證；A1/A2 live URL 列 operator 設定（I/O 邊界）

## post-Deploy
`telemetry(行政區覆蓋/事故點數/refused 率) → validate → Delta`。
未竟（範圍外）：斷路器（Gateway Router REQ:GW:ROUTER:003 落地後上移）、A1/A2 specific dataset 自動發現、TDX 即時站點。
