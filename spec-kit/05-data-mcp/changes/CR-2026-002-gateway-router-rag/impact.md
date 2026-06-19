# Impact Analysis — CR:2026:002 Gateway Router + RAG Adapter

> 治理頁 03 八項必查。結論：**修改 `gateway-compliance.md` 一處 + 新增品質 Profile；無 breaking change；觸及 Inv-1/Inv-7 的執行面（強化、非變更語意）→ Domain Review**。

| # | 檢查項 | 結果 |
|---|---|---|
| 1 | Domain invariant 是否改變 | **語意未變，執行面強化**。RAG Adapter 是 Inv-1/Inv-7 在檢索路徑的執行點 → 走 **Domain Review**（確認不變量未被弱化） |
| 2 | 資料模型/migration | **無**新表（Router/RAG 為無狀態插件；斷路器狀態存 Redis，非 schema） |
| 3 | API contract 破壞既有 consumer | **否**。Router 對既有 tool 透明；RAG 在檢索層加過濾，不改 tool 簽名 |
| 4 | UI state / error handling | 復用既有錯誤碼（`source_unavailable`/`SOURCE_QUOTA_EXCEEDED`）；無新增 |
| 5 | BDD scenario | **新增** `gateway-router.feature`、`gateway-rag.feature`；與既有無衝突 |
| 6 | Quality profile | **新增** `QP:GATEWAY:STANDARD`（hot-path 低延遲）；不影響既有 QP |
| 7 | 既有測試失效 | **否**。新增獨立 feature |
| 8 | 監控/告警/Runbook | **是**。新增 Router fallback/斷路器觸發率、RAG 越界攔截數（`TenantScopeViolationDetected`）指標 → GATE:DEPLOY |

## 風險

| 風險 | 緩解 |
|---|---|
| RAG 未強制 tenant scope → prompt injection 跨租戶外洩（H1） | REQ:GW:RAG:002 硬約束 + 越界告警；Domain Review 確認 |
| Router fallback 誤降到禁用源（591/leju） | REQ:GW:ROUTER:002 明禁；DI-4 黑名單雙重保險 |
| Gateway 插件成為 hot-path 瓶頸 | QP:GATEWAY:STANDARD 低延遲門檻（GATE:VDD 驗） |

## 裁決

走 **Domain Review**（RAG 觸及 Inv-1/Inv-7 執行面）→ 確認不變量未弱化 → GATE:SPEC。
