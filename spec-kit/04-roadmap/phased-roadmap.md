# 分階段 Roadmap 與 Go/No-Go Gates

> 對應報告第 7 節。**Gate 未過不得前進**。本 roadmap 是技術落地順序，**不解除商業關卡**（Gate A）。

## 一圖總覽

```
Gate A (商業, 寫 code 前)  ──┐
  ≥5 房仲預付承諾            │ 未過→停
                            ▼
Phase 0  多租戶/PII/治理 ──── Gate B (合規) ── 未過→禁接 mem0/真實客戶資料
  (上線 blocker)              @gateB 全綠
                            ▼
Phase 1  文案/說帖 killer ── 破冰：零輸入/零延遲/無錯價風險
                            ▼
Phase 2  客戶記憶+配對 ────── Gate C (成本) ── per-seat 覆蓋月變動成本
  (護城河, 與MVP同步)
                            ▼
Phase 3  行情輔助(降級) ───── 錯價防護就緒才上
Phase 4  說明書/Flex/排約 ── 進階
```

## 各階段

### Phase 0 — 多租戶 + PII + 治理（上線 blocker）
- **里程碑**：`erm.dbml` schema 落地；`tenant_id` 雙層 scope；資料存取層強制 `WHERE tenant_id`（Inv-1，typed query builder 禁裸 SQL）；HITL gate + 逾時（Inv-2）；append-only audit 含 `correlation_id/causation_id/actor_type`（Inv-3，REVOKE UPDATE/DELETE）；PII 脫敏最小集（Inv-8）；**資料保留與被遺忘權流程（Inv-10）**；TimestampGuard 元件（Inv-4，供 Phase 3）；per-tenant 並發閘（REL-2）。
- **驗收**：`@gateB` 全綠（[`tenant-isolation`](../03-features/phase0-tenant-isolation.feature) + [`pii-governance`](../03-features/phase0-pii-governance.feature) + [`hitl-audit`](../03-features/governance-hitl-audit.feature)），由 CI required check 強制。
- **緩解**：MVP 用部署隔離（一店一 home）跑單店，規避動核心；隔離仍以 dual-tenant CI fixture 驗（Inv-1 測試策略）。
- **參考**：[`repo-layout.md`](repo-layout.md)、[`deployment.md`](deployment.md)。
- **資源**：後端 + 安全。

### Phase 0.5 — 付費意願 POC（Gate A，商業 go/no-go）
- **里程碑**：雙訊號付費 Discovery（先 NT$20–40k 測肯不肯付，綠燈再測願付多少）；向 2–3 家**非友情**同業。
- **關卡**：無 ≥5 預付承諾**不開發 production**。
- **資源**：BD/PM。**註**：此關屬商業驗證，不在 BDD 範圍。

### Phase 1 — 第一週 killer
- **里程碑**：物件文案/標題生成 + 帶看捷運機能說帖。
- **複用**：對話主腦 + LINE + STT + vision，零核心改動。
- **驗收**：[`listing-copywriting`](../03-features/phase1-listing-copywriting.feature) + [`viewing-briefing`](../03-features/phase1-viewing-briefing.feature)。
- **價值**：當天有感、無錯價風險破冰。

### Phase 2 — 留存核心（與 MVP 同步，護城河）
- **里程碑**：結構化客戶/物件 store + SQL WHERE 配對 + 主動跟進提醒；Gate B 後接 mem0（tenant-scoped）。
- **驗收**：[`customer-memory`](../03-features/phase2-customer-memory.feature) + [`matching`](../03-features/phase2-matching.feature)。
- **風險**：資料輸入意願是致命假設（H5），先 POC 驗過再押注；語音/STT 降門檻。
- **Gate C**：per-seat 定價覆蓋每客戶月變動成本（LLM+Push）。

### Phase 3 — 行情輔助（降級，錯價防護就緒才上）
- **里程碑**：lvr-trades domain tool（ACL）+ 完整防護鏈。
- **驗收**：[`market-comp-guardrail`](../03-features/phase3-market-comp-guardrail.feature)。
- **話術**：「近 N 季官方彙整 + 趨勢」，禁稱即時。

### Phase 4 — 進階
- 說明書檢核 checklist（強制人工簽核）+ Flex 卡 + 多方排約。OCR field-level 漏項率未達標不上線。

### 工程韌性（並行）
- 並發 Semaphore（REL-2）；狀態外移 Redis（REL-1/Inv-9）；Push 額度監控（COST-3）；負載+成本壓測。

---

## Go/No-Go 關卡彙整

| Gate | 階段 | 條件 | 未過 |
|---|---|---|---|
| **A 商業** | 0.5 | ≥5 房仲預付承諾 | 停，回評 per-seat / 換垂直 |
| **B 合規** | 0 | `@gateB` 全綠（Inv-1/2/3/8 + RAG 硬約束） | 禁接 mem0、禁接真實客戶資料 |
| **C 成本** | 2 | per-seat 覆蓋月變動成本 | 重新定價 / 限縮高 token 功能 |

---

## 止損紅燈（來源報告 Part II/III）

- 6 個月拿不到第二個付費客戶 → 垂直選錯，重估。
- 模組複用率 < 30% → 護城河證偽，下修定位。
- 診斷收不到錢 → 顧問價值在房仲垂直證偽，回評 B2B per-seat。
- 任一房仲回報錯價 → 北極星反指標，功能停損檢討。
