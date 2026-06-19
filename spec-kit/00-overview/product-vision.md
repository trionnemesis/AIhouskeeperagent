# 產品願景與設計前提

## 一句話定位

> 把房仲散落在 **LINE / Excel / 人腦 / 多個外部系統** 的工作，重新設計成具備**記憶、工具操作、主動提醒、人工審核（HITL）**的 AI Agent Workflow——以 Hermes-Agent 為 runtime 底座，mem0 為長期記憶，LINE 為唯一觸點。

賣的是**判斷與流程重設計**，不是 bot 功能。技術底座大量現成；產品/商業案尚未驗證。

---

## 被推翻的假設（來源報告審查結論，務必內化）

| 草案假設 | 審查裁決 | 對 spec 的影響 |
|---|---|---|
| 「即時行情引擎」是 killer feature 與護城河 | **一致推翻** | 行情降級為輔助（Phase 3），需錯價防護；**不可當門面** |
| 實價登錄 + twtools = 數據護城河 | **一致推翻**（公開免費 + 共用 MCP，零門檻可複製） | 護城河改為「結構化客戶記憶 + 配對 + 工作流嵌入」的切換成本 |
| session 隔離（每客戶）現成 | **推翻**（`session_key` 是路由 key，非租戶邊界） | 多租戶 / PII 隔離降級為「需新增」，提前到 Phase 0 |
| PII 合規排 Phase 3 | **推翻**（是准入門檻） | 提前到 Phase 0，列為上線 blocker |
| 結構化客戶記憶排 Phase 2 次要 | **認可定位但提前** | 與 MVP 同步，是 Core Domain |

---

## 設計原則（從報告萃取為工程約束）

1. **隔離優先（Isolation-first）**：隔離不變量未就緒前，**禁接向量記憶（mem0）**、禁接真實客戶 PII。見 [`../01-domain/invariants.md`](../01-domain/invariants.md)。
2. **無錯價風險優先（No-mispricing-first）**：第一週價值用「零輸入、零延遲、無錯價風險」的文案/說帖破冰；任何不確定的行情查詢一律**拒答**而非猜測。
3. **人工核准優先（HITL-first）**：所有對外訊息與寫入動作，必過 HITL gate。HITL 軌跡同時是**法律免責證據鏈**。
4. **信任即 KPI（Trust-as-KPI）**：北極星追蹤「AI 報錯價 / 錯資訊」次數，錯誤即停損。見 [`north-star-and-gates.md`](north-star-and-gates.md)。
5. **底座 pin 版本**：Hermes 是活躍開發 codebase，production **pin 版本不跟 main**，避免追 breaking change 的隱形維運稅。
6. **新 code 進 Node.js 層**：Hermes（Python runtime）原則上**零核心改動複用**；領域 / 治理 / 整合的新邏輯一律寫在 Node.js 層（domain MCP servers + 治理 middleware + 多租戶 LINE gateway）。見 [`../02-spec/system-architecture.md`](../02-spec/system-architecture.md)。

---

## MVP 三階段聚焦

```
Phase 0 (blocker)   多租戶 / PII 隔離 + 治理最小集
        │           └─ 不過此關，不接真實客戶資料、不接 mem0
        ▼
Phase 1 (killer)    物件文案 / 帶看說帖生成
        │           └─ 零輸入、零延遲、當天有感、無錯價風險（破冰）
        ▼
Phase 2 (護城河)    結構化客戶記憶 + SQL WHERE 配對
                    └─ 切換成本與留存來源；mem0 tenant-scoped 接入
```

行情輔助（Phase 3）與說明書檢核（Phase 4）在 MVP 範圍外，僅在 Context Map 與 roadmap 標示，並保留錯價防護規格作為接入前置條件。

---

## 非目標（Out of Scope，刻意排除）

- ❌ 把行情當門面 / killer feature。
- ❌ 在隔離不變量就緒前接 mem0 或任何向量記憶。
- ❌ AI 自動對外發訊息 / 自動寫入客戶系統（必經 HITL）。
- ❌ B2C freemium 作為主力獲客（無數據前僅作 pilot 試用層）。
- ❌ 跨租戶資料聚合 / 推薦。
- ❌ 多平台物件自動同步發佈（Phase 4+）。

---

## 與來源報告的對應

本 spec kit 實作報告第 2.4 節列出的底座缺口與第 4.3 節領域模型骨架，並補上報告明確點名缺漏的兩份 SDD 產物：`spec/erm.dbml` 與 `features/*.feature`。
