# BDD 行為規格（Features）

> Gherkin `.feature`，可由 Cucumber.js 執行。語言 `zh-TW`（繁中關鍵字 `假設/當/那麼/而且/但是`），technical terms 保留英文。
> 每個場景對應領域事件與不變量；治理場景優先（P0）。

## 檔案對照

| 檔案 | Context | Phase | 對應不變量/事件 |
|---|---|---|---|
| [`phase0-tenant-isolation.feature`](phase0-tenant-isolation.feature) | C1/C2 | 0 (Gate B) | Inv-1, TenantScopeViolationDetected |
| [`phase0-pii-governance.feature`](phase0-pii-governance.feature) | C2 | 0 (Gate B) | Inv-2/3/8, PiiAccessLogged |
| [`governance-hitl-audit.feature`](governance-hitl-audit.feature) | C2 | 0 (橫切) | Inv-2/3, HITLApproved/Rejected, MispricingReported |
| [`phase1-listing-copywriting.feature`](phase1-listing-copywriting.feature) | C4 | 1 (killer) | ListingCopyGenerated/Approved |
| [`phase1-viewing-briefing.feature`](phase1-viewing-briefing.feature) | C4 | 1 | ViewingBriefingGenerated |
| [`phase2-customer-memory.feature`](phase2-customer-memory.feature) | C5 | 2 (核心) | CustomerRequirementDrafted/Profiled/MemoryWritten, Inv-7 |
| [`phase2-matching.feature`](phase2-matching.feature) | C6 | 2 (核心) | MatchCandidatesProduced/MatchPresented, Inv-1 |
| [`interaction-logging.feature`](interaction-logging.feature) | C5/C7 | 2 | InteractionLogged |
| [`phase3-market-comp-guardrail.feature`](phase3-market-comp-guardrail.feature) | C8 | 3 (降級) | MarketCompProvided/Refused, Inv-4/5/6, REL-4 |
| [`governance-concurrency.feature`](governance-concurrency.feature) | C2 | 0 | REL-2, CONCURRENCY_LIMITED |

## 執行

設定見 [`cucumber.js`](cucumber.js)；step 骨架見 [`steps/`](steps/)（`support/world.ts` 注入 ctx、`definitions/shared-steps.ts` 共用中文 step 綁定範例）。CI 把關見 [`../.github/workflows/bdd-gate-b.yml`](../.github/workflows/bdd-gate-b.yml)。

```bash
# 於 spec-kit/ 根目錄（已備 package.json / tsconfig.json）
npm install                      # 安裝 @cucumber/cucumber + ts-node（無 committed lockfile，故用 install）
npm run bdd                      # 全部（預設 profile）
npm run bdd:gateB                # 僅 Gate B 驗收（@gateB）
```

> ⚠️ step 骨架為 spec-level；領域特定步驟（行情防呆/HITL/冪等/並發）需在實作 repo 接上真實 SUT。未綁定步驟 cucumber 報 undefined（CI 視為失敗）——這正是 Gate B 不被虛設的保證。

## Tag 慣例

- `@gateB`：Phase 0 合規關卡驗收（必綠才接真實客戶資料）
- `@core`：護城河核心（C5/C6）
- `@governance`：治理橫切
- `@guardrail`：錯價防護（C8）
- `@p0 @p1 @p2 @p3`：phase 標記

## 與 Gate 的關係

> `@gateB` 全綠是「接 mem0 / 接真實客戶 PII」的前置條件（見 [`../00-overview/north-star-and-gates.md`](../00-overview/north-star-and-gates.md)）。商業 Gate A（付費意願）不在 BDD 範圍——那是 POC 驗證，不是程式行為。
