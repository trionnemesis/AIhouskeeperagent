# Traceability — CR:2026:001 public-safety-mcp

> 最小格式（治理頁 07）。每個 Requirement ID 串起 domain invariant → BDD → API → test → red evidence → mutation → quality → telemetry。
> `⏳` = 實作期產生（spec 階段預先佈線）。

## REQ:PUBSAFE:001 — 交通事故周邊密度

```
REQ:PUBSAFE:001
  ├─ Domain Invariant : DI-5(粒度封頂), DI-3(時點), DI-2(顯名), Inv-4(TimestampGuard), Inv-5(拒答)
  ├─ BDD Scenario     : features/public-safety.feature「交通事故以周邊密度聚合呈現」「點位不外洩為門牌」
  ├─ UI State         : UI:PUBSAFE:* (Loading/Error/Empty/Disabled，委派 line-channel)
  ├─ API Contract     : TOOL:PUBSAFE:001 traffic_accident_density()
  ├─ Data             : DATA:traffic_accidents (erd.dbml)
  ├─ Test             : ⏳ unit(密度聚合)/feature/contract
  ├─ Red Evidence     : ⏳ baseline 失敗證據
  ├─ Mutation Result  : ⏳ 粒度/聚合邏輯殺變異
  ├─ Quality Verify   : QP:DATA-MCP:READ + GATE:VDD domain_specific(granularity_cap)
  └─ Production Telemetry : ⏳ 治安查詢用量 + DI-5 違規計數
```

## REQ:PUBSAFE:002 — 區域治安統計

```
REQ:PUBSAFE:002
  ├─ Domain Invariant : DI-5(禁套物件/禁負面標籤), DI-3, DI-2, Inv-5
  ├─ BDD Scenario     : 「區域統計止於鄉鎮市區」「禁套單一物件」「禁負面標籤」
  ├─ UI State         : UI:PUBSAFE:*
  ├─ API Contract     : TOOL:PUBSAFE:002 area_crime_stats()
  ├─ Data             : DATA:crime_area_stats (dataset 14200)
  ├─ Test             : ⏳ + 負向(門牌請求被拒/標籤被攔)
  ├─ Red Evidence     : ⏳
  ├─ Mutation Result  : ⏳
  ├─ Quality Verify   : GATE:VDD domain_specific(no_negative_labels, area_stat_not_applied_to_listing)
  └─ Production Telemetry : ⏳
```

## REQ:PUBSAFE:003 — 防詐查核（P3）

```
REQ:PUBSAFE:003
  ├─ Domain Invariant : DI-2, DI-3, Inv-5
  ├─ BDD Scenario     : 「165 涉詐網站命中/未命中」
  ├─ API Contract     : TOOL:PUBSAFE:003 fraud_check()
  ├─ Data             : DATA:fraud_domains (165 CSV)
  ├─ Test/Red/Mutation/Quality/Telemetry : ⏳（P3，可後置）
```

## 證據存放

- Red Evidence / mutation / quality reports：實作 repo `test/evidence/CR-2026-001/`（per gates.md）。
- 本 spec 階段佈線 Stable ID 與 Gate 條件，實作期填入 `⏳` 證據。
