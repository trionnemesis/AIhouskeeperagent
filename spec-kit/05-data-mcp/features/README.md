# 資料 MCP BDD 場景

> Gherkin `zh-TW`。**已接入** 主 spec kit cucumber 基建：[`../../03-features/cucumber.js`](../../03-features/cucumber.js) 的 `paths`/`require` 已含 `05-data-mcp/features/**`，[`steps/data-steps.ts`](steps/data-steps.ts) 提供資料層共用斷言（沿用 03 的 World + shared-steps），[Gate B CI](../../.github/workflows/bdd-gate-b.yml) `paths` 已含本層。執行：於 spec-kit 根 `npm run bdd` / `npm run bdd:gateB`。

## 檔案對照

| 檔案 | Server/層 | 對應不變量 |
|---|---|---|
| [`lvr-market.feature`](lvr-market.feature) | lvr-mcp (P0) | Inv-4/5/6, DI-2/3/9, REL-4 |
| [`gateway-pii-egress.feature`](gateway-pii-egress.feature) | Gateway PII (P0) | **DI-1**, Inv-8 |
| [`gateway-toolauthz-blacklist.feature`](gateway-toolauthz-blacklist.feature) | Gateway ToolAuthZ | **DI-4**, DI-8 |
| [`gateway-policy-disclosure.feature`](gateway-policy-disclosure.feature) | Gateway Policy | DI-2/3/5 |
| [`amenities-geocoding.feature`](amenities-geocoding.feature) | amenities-mcp (P1) | DI-6/7/8/2, REL-4 |
| [`company-resolve.feature`](company-resolve.feature) | company-registry (P2 部分) | DI-1/8 |
| [`public-safety.feature`](public-safety.feature) | public-safety (P2) | **DI-5**(粒度封頂), DI-2/3/7/8, Inv-4/5, REL-4 |
| [`gateway-router.feature`](gateway-router.feature) | Gateway Router (CR-2026-002) | DI-4(禁降黑名單)/DI-8, REL-4, 斷路器 |
| [`gateway-rag.feature`](gateway-rag.feature) | Gateway RAG Adapter (CR-2026-002) | **Inv-1/Inv-7**(越界防線 H1), DI-1/6/7 |

> `public-safety.feature` 依 STDD×VDD 產出：每場景須先過 **GATE:RED**（baseline 失敗 + Red Evidence），斷言業務結果（非僅 status），含 DI-5 負向場景；Change Package 見 [`../changes/CR-2026-001-public-safety/`](../changes/CR-2026-001-public-safety/)。

## Tag

- `@data`：資料層
- `@gateway`：AI Gateway WASM 合規
- `@gateB`：合規關卡（PII/黑名單）——延用主 spec Gate B 精神，接真實資料前須綠
- `@p0/@p1/@p2`：優先序

## 範圍外（本輪不寫）

- public-safety-mcp（P2，列於決策矩陣待後續）
- 建案↔起造人（blocked-on Q1）、承造人/營造廠（P3）
- 591/leju 爬取場景（黑名單，僅以「禁用」場景驗收）
