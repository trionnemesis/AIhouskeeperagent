# Change Intent — CR:2026:002 AI Gateway Router + RAG Adapter

> STDD×VDD Change Package。補完使用者參考架構中 AI Gateway 5 個 WASM 插件的最後兩個（Router、RAG Adapter），原為「輕描述」。

## Change Intent

把 `gateway-compliance.md` 的 Router / RAG Adapter 從「相鄰、輕描述」升級為**完整可驗證規格**，完成 5 插件閘（Policy/PII/Router/ToolAuthZ/RAG）。

## 動機

- 參考架構明列 5 個 WASM 插件；Router/RAG 未深規格 = 架構缺口。
- RAG Adapter 是**檢索路徑的 prompt-injection→RAG 越界（H1）最後防線**，必須與 PII/ToolAuthZ 同級為不可繞過邊界。
- Router 的多源 fallback + 斷路器是 REL-4 降級與 DI-8 配額保護的執行點。

## 邊界（STDD 硬約束）

- Router 路由表為**設定（deterministic）**，非 LLM 判斷；fallback **不得**降到禁用源（591/leju 永禁，DI-4）。
- RAG 檢索一律強制 tenant scope（Inv-1）+ mem0 namespace（Inv-7）+ PII 過濾（DI-1）。
- 不引入新外部依賴（延續 Twinkle 不消費決策）。

## Definition of Ready

- [x] Change Intent（本檔）
- [x] Delta Spec（[`delta.yaml`](delta.yaml)）
- [x] Impact Analysis（[`impact.md`](impact.md)）
- [x] 受影響 Stable ID 已列出
- [x] Acceptance（[`../../features/gateway-router.feature`](../../features/gateway-router.feature)、[`../../features/gateway-rag.feature`](../../features/gateway-rag.feature)）
- [x] Verification Plan（[`verification-plan.yaml`](verification-plan.yaml)）
