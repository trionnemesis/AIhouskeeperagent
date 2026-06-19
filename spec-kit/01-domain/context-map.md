# Bounded Context Map（全域）

> 全產品 8 階段價值鏈映射成 Bounded Context（廣度，輕量）。標示 subdomain 類型與 MVP 範圍。

## Subdomain 分類

| 類型 | 意義 | 投資原則 |
|---|---|---|
| ★ **Core** | 護城河所在，差異化來源 | 自建、投最多心力 |
| ○ **Supporting** | 必要但非差異化 | 務實實作，可外包/簡化 |
| ◇ **Generic** | 通用能力 | **複用現成**（Hermes / mem0 / 第三方） |
| ⊞ **Cross-cutting** | 橫切所有 context | 統一治理層 |

---

## Context 清單

| # | Bounded Context | 價值鏈階段 | Subdomain | MVP | 底座 |
|---|---|---|---|---|---|
| C1 | **Identity & Tenancy** 租戶/身分/隔離 | （全程前置） | ◇ Generic（但約束關鍵） | ✅ Phase0 | 🔴 需新增 |
| C2 | **Governance & Compliance** 治理/HITL/audit/PII | （橫切） | ⊞ Cross-cutting | ✅ Phase0 | 🟡 部分（approval）/🔴 audit |
| C3 | **Conversation Runtime** 對話 runtime | （承載） | ◇ Generic | ✅ 複用 | 🟢 Hermes |
| C4 | **Content Generation** 文案/說帖 | 物件管理/帶看 | ○ Supporting¹ | ✅ Phase1 | 🟢 主腦/🔴 prompt+skill |
| C5 | **Customer & CRM** 結構化客戶記憶 | 客源/售後 | ★ **Core** | ✅ Phase2 | 🟡 mem框架/🔴 schema |
| C6 | **Matching** 買賣媒合配對 | 買賣媒合 | ★ **Core** | ✅ Phase2 | 🔴 需新增 |
| C7 | **Interaction & Scheduling** 帶看/斡旋/跟進/排程 | 帶看/議價 | ○ Supporting | 部分（跟進提醒） | 🟢 Cron/🔴 排程協調 |
| C8 | **Market Intelligence** 行情輔助 | 委託/議價 | ○ Supporting（降級） | ⛔ Phase3 | 🟢 源/🔴 ACL+防護 |
| C9 | **Notification** 主動推播 | （售後/全程） | ○ Supporting | ✅ Phase2 | 🟢 Cron+LINE Push |
| C10 | **Contract & Disclosure** 簽約/說明書檢核 | 簽約 | ○ Supporting | ⛔ Phase4 | 🟡 OCR/vision |
| C11 | **Listing**（物件生命週期，aka C-Listing） | 物件管理 | ○ Supporting | ✅ Phase2 | 🔴 需新增 |

> **C-Listing = C11**：`Listing` 聚合的唯一邏輯 owner，擁有完整生命週期事件（`ListingProfiled`/`ListingDelisted`）。C4（文案）/C6（配對）以 `listing_ref` 參照、不共享聚合。aggregates.md / domain-events.md / glossary.md 一律以 **C-Listing** 指稱本 context。

> ¹ C4 為 **Supporting**（非長期護城河，差異化來源是 C5/C6），但同時是 **Phase 1 獲客 killer**，故 roadmap 優先序高。**subdomain 分類（差異化軸）與 roadmap 優先序（獲客軸）是兩個獨立的軸**，勿混淆。見 event-storming §2、product-vision Phase 1。

---

## Context Map（關係與整合模式）

```
                          ┌─────────────────────────────────────────┐
                          │  ⊞ C2 Governance & Compliance            │
                          │  (隔離不變量 / HITL / audit / PII)        │  ← 橫切約束所有 context
                          └─────────────────────────────────────────┘
                                          ▲ conformist (所有下游遵從治理規則)
   ┌──────────────┐                       │
   │ C1 Identity  │── upstream (U) ───────┤
   │  & Tenancy   │   提供 tenant scope    │
   └──────────────┘                       │
          │ scope                          │
          ▼                                │
   ┌────────────────────────────────────────────────────────────────┐
   │      ◇ C3 Conversation Runtime (Hermes) = Open Host Service (OHS) │
   │   對話迴圈 · 工具註冊 · prompt builder · LINE adapter · STT       │
   └────────────────────────────────────────────────────────────────┘
        │ tool call (OpenAI-compatible / MCP)
        ├──────────────┬──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ C4      │   │ ★C5     │   │ ★C6     │   │ C8      │   │ C9      │
   │ Content │   │Customer │──▶│ Matching│   │ Market  │   │ Notify  │
   │ Gen     │   │ & CRM   │   │         │   │ Intel   │   │         │
   └─────────┘   └────┬────┘   └─────────┘   └────┬────┘   └─────────┘
                      │ ACL                        │ ACL (防髒資料)
                      ▼                            ▼
                 🩷 mem0 MCP                   🩷 lvr-trades MCP
              (tenant-scoped 強制)          (TimestampGuard 過濾)

   (C-Listing/C11：Listing 與 C5 同庫，與 C5 並列供料給 C6；圖省略其框，見下表 C5/C-Listing→C6)
```

### 關鍵整合關係

| 關係 | 模式 | 說明 |
|---|---|---|
| C1 → 所有 | Upstream/Downstream (U/D) | Tenancy 提供 `tenant_id` scope，下游一律遵從 |
| C2 ↔ 所有 | Conformist | 所有 context 必須遵從治理不變量，無協商空間 |
| C3 | **Open Host Service (OHS) / Conformist** | Hermes runtime 承載對話；本專案 pin 版本、零核心改動（product-vision §5-6），domain context 以 tool/MCP 接入。下游遵從上游 API，**無共享所有權**（非 Shared Kernel——標 Shared Kernel 會誤導團隊以為可改 Hermes 核心） |
| C5 → 🩷 mem0 | **Anti-Corruption Layer (ACL)** | mem0 呼叫**強制** namespace = `tenant_id:seat_id:customer_id`（見 mem0-integration.md） |
| C8 → 🩷 lvr-trades | **Anti-Corruption Layer (ACL)** | 包裝外部髒資料，TimestampGuard + 單價檢核 + 拒答邏輯 |
| C5 / C-Listing → C6 | **Co-located Aggregates (MVP)** | **co-location（物理）**：MVP 期 Customer（C5）與 Listing（C-Listing）共用同一 Node.js Domain DB，MatchingService（C6）以 SQL WHERE 跨表直讀（event-storming §5），Inv-1 在資料層強制。**ownership（邏輯）**：Customer 屬 C5、Listing 屬 C-Listing，C6 不擁有任一聚合。**規模化轉 Published Language**（`CustomerRequirementUpdated`/`ListingProfiled`→`MatchCandidatesProduced`），屆時為 Customer-Supplier |
| C5/C6 → C9 | Published Language (event) | 透過 domain event 觸發推播 |
| C7 → C9 | Published Language (event) | `FollowUpTaskScheduled` 到期 → C9 推播（排程/送達職責分離） |

---

## 為什麼 mem0 與 lvr 都用 ACL？

兩者都是**不受控的外部資料源**：
- **mem0**：第三方記憶服務，若不在 ACL 強制 tenant 命名空間，prompt injection 或檢索越界即跨租戶 PII 外洩（H7）。
- **lvr-trades**：第三方 MCP，資料含垃圾值與延遲（H3/H4）。ACL 是「**防止外部模型的髒概念污染領域模型**」的標準 DDD 手段。

> ACL 不是可選項，是 Phase 0 合規 gate 的一部分。
