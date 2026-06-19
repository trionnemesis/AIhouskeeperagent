# Traceability — CR:2026:002 Gateway Router + RAG Adapter

> 最小格式（治理頁 07）。`⏳` = 實作期產生。

## REQ:GW:ROUTER:001/002/003 — 來源路由 / fallback / 斷路器

```
REQ:GW:ROUTER:001-003
  ├─ Domain Invariant : DI-4(禁降禁用源), DI-8(配額/斷路), REL-4(降級不崩)
  ├─ BDD Scenario     : gateway-router.feature（路由/多源fallback/全失效降級/斷路器/禁降黑名單）
  ├─ API Contract     : Gateway 插件（對 tool 透明）
  ├─ Test             : ⏳ unit(路由表/fallback順序/斷路器狀態機)
  ├─ Red Evidence     : ⏳
  ├─ Mutation Result  : ⏳（路由/fallback 邏輯）
  ├─ Quality Verify   : QP:GATEWAY:STANDARD + GATE:VDD resilience
  └─ Production Telemetry : ⏳ fallback 率 / 斷路器觸發
```

## REQ:GW:RAG:001-004 — PII 過濾 / tenant scope / provenance 排序 / 去重

```
REQ:GW:RAG:001-004
  ├─ Domain Invariant : Inv-1(tenant scope), Inv-7(mem0 ns), DI-1(PII), DI-7(provenance), DI-6(低信心)
  ├─ BDD Scenario     : gateway-rag.feature（越界丟棄+告警/PII過濾/authority排序/去重）
  ├─ API Contract     : 檢索層插件（對 tool 透明）
  ├─ Test             : ⏳ + 負向(跨租戶檢索回空+TenantScopeViolationDetected)
  ├─ Red Evidence     : ⏳
  ├─ Mutation Result  : ⏳（scope/過濾/排序）
  ├─ Quality Verify   : GATE:VDD security_domain（machine-checkable）
  └─ Production Telemetry : ⏳ RAG 越界攔截數
```
