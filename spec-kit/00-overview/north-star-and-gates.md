# 北極星 KPI 與 Go/No-Go Gates

## 北極星 KPI：信任（Trust），不是功能數

> 這個產品最大的敵人不是技術缺口，是 **房仲對 AI 報錯價的零容忍 × 巨頭免費 AI × 資料輸入意願** 這三道牆。

**主指標**

| KPI | 定義 | 目標方向 |
|---|---|---|
| 錯誤回報數 | 房仲回報「AI 報錯價 / 錯資訊」次數 | **趨近 0**（反指標，越低越好） |
| HITL 採納率 | 經紀人核准 AI 草稿（不修改）的比例 | 上升 = 信任上升 |
| 留存 / 切換成本 | 結構化客戶記憶累積量 × 持續使用天數 | 上升 = 護城河形成 |

**反指標停損規則**：任一房仲回報一次錯價 → 觸發 `MispricingReported` 事件 → 該功能立即停損檢討（見 [`../03-features/governance-hitl-audit.feature`](../03-features/governance-hitl-audit.feature)）。

---

## Go/No-Go Gates（關卡，未過不得前進）

### Gate A — 商業關卡（Phase 0.5，寫 production code 前）
- **條件**：≥ 5 位房仲**預付承諾**（非友情價）。
- **驗證**：雙訊號付費 Discovery（先低額 NT$20–40k 測「肯不肯付」，綠燈再測「願付多少」）。
- **未過**：停。回評 B2B per-seat 或換垂直。
- **狀態**：⛔ 本 spec kit 不假設此關已過；spec 是「技術怎麼蓋」，不解除此關卡。

### Gate B — 合規關卡（Phase 0）
- **條件**：隔離不變量 `WHERE tenant_id=?` 就緒（含 RAG 硬約束）+ PII 最小治理集（HITL 全核准 + 不寫真 PII / 用代號脫敏 + 時間戳防呆）。
- **未過**：**禁接 mem0、禁接真實客戶資料**。
- **驗收**：[`../03-features/phase0-tenant-isolation.feature`](../03-features/phase0-tenant-isolation.feature) + [`../03-features/phase0-pii-governance.feature`](../03-features/phase0-pii-governance.feature) + [`governance-hitl-audit`](../03-features/governance-hitl-audit.feature) 全綠。
- **強制機制**：由 CI `@gateB` job 把關（[`../.github/workflows/bdd-gate-b.yml`](../.github/workflows/bdd-gate-b.yml)），設為 required status check；未綠不得 merge / 部署 / 開 `MEM0_ENABLED`。否則 Gate 形同虛設。

### Gate C — 成本關卡（壓測）
- **條件**：per-seat 定價（估計 NT$300–600）能覆蓋每客戶月變動成本（LLM token + LINE Push）。
- **機制**：強模型場景設 `iteration_budget` / token 上限，鎖死每 session 成本。
- **未過**：重新定價或限縮高 token 功能。

---

## 三道牆與緩解對照

| 牆 | 內容 | spec 對應緩解 |
|---|---|---|
| 牆 1 | 房仲對錯價零容忍 | 錯價防護 + 拒答優於猜測 + 行情降級 + 北極星反指標 |
| 牆 2 | 巨頭免費內建 AI（信義/永慶/591…） | 賣流程重設計與切換成本，不比 bot 功能；護城河 = 結構化記憶 |
| 牆 3 | 資料輸入意願（delayed payoff） | 第一週用零輸入的文案/說帖破冰；客戶記憶用 LINE 語音/STT 降低輸入門檻 |

---

## 開放分歧（需 POC 解決，spec 不假裝有答案）

| 分歧 | 立場 A | 立場 B | 解法 |
|---|---|---|---|
| 多租戶實作 | 應用層 schema（tenant_id 欄位） | 部署隔離（一店一 home） | **MVP 用部署隔離跑單店**，規模化再評估應用層（見架構文件） |
| 結構化記憶可行性 | MVP 雙核心之一 | 依賴行為改變，可能落空 | 5–10 位房仲 POC 驗「輸入意願」再押注 |
| B2C freemium 角色 | 主力獲客 | 補貼不付費者 | 僅作 pilot 試用層，無數據前不主推 |
