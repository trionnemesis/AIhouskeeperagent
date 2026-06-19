# 事件風暴地圖（Event Storming）

> DDD Big Picture → Process Modeling。色票：
> 🟠 **Domain Event**（已發生，過去式）· 🔵 **Command**（觸發事件的命令）· 🟡 **Actor**（角色）·
> 🟫 **Aggregate**（一致性邊界）· 🟪 **Policy**（whenever…then… 反應規則）· 🟩 **Read Model**（決策視圖）·
> 🩷 **External System** · 🟥 **Hotspot**（風險/未決）
>
> 治理是 cross-cutting：**每一條 Command 都先過治理閘**（隔離 scope 注入 → 風險判定 → 必要時 HITL）。詳見 [`invariants.md`](invariants.md)。

---

## 0. 全域時間線（Big Picture，左→右）

```
委託/開發 ── 物件管理 ── 客源開發 ── 買賣媒合 ── 帶看 ── 斡旋/議價 ── 簽約 ── 售後
   │            │           │           │         │        │          │       │
 (Phase3+)   Listing     Customer    Matching  Briefing  MarketComp  (P4)   FollowUp
                          ★Core       ★Core    Phase1   Phase3                Phase2
```

MVP 深規格聚焦：**內容生成（Phase1）** + **客戶記憶/配對（Phase2）** + **治理（Phase0, cross-cutting）**。

---

## 1. 🟥 Hotspots（先標風險，再設計）

| # | Hotspot | 來源 | 處置 |
|---|---|---|---|
| H1 | `session_key` 非租戶邊界，跨客戶 PII 外洩風險 | 報告 2.4 | 隔離不變量（Inv-1）+ Phase0 gate |
| H2 | in-memory dedup/reply token，重啟即遺失 → 重複回覆 + 重複燒 Push | 報告 2.3 | 狀態外移（Redis）+ 冪等 key |
| H3 | lvr 日期垃圾值（2101/2033/1921）→ 錯價 | 報告實測 | TimestampGuard（Inv-4）+ 拒答 |
| H4 | 行情延遲 3–5 月，房仲一看 `trade_date` 即識破 | 報告實測 | 延遲聲明 + 降級為輔助 |
| H5 | 結構化記憶要房仲主動輸入（delayed payoff） | PMF 審查 | 語音/STT 降門檻 + 第一週用零輸入破冰 |
| H6 | 並發 agent run 無 Semaphore | 報告 2.3 | 並發閘（NFR） |
| H7 | mem0 在隔離未就緒前接入 = 跨租戶越界 | 審查硬條件 | mem0 ACL 強制 tenant scope（見 mem0-integration） |

---

## 2. 流程：物件文案生成（Phase 1 · Killer · 無錯價風險）

```
🟡 經紀人
  └🔵 提交物件照片/重點 (LINE 文字/圖片)
      └[治理閘: 注入 tenant_id+seat_id, 風險=低]
        └🟫 CopywritingSession
            ├🩷 Hermes 對話迴圈 (LLM + vision)
            └🟠 物件文案已生成  ListingCopyGenerated
                └🟪 Policy: 文案產生後 → 進入 HITL 等待核准 (草稿不外流)
                    └🔵 經紀人核准/編輯文案
                        └🟠 文案已核准  ListingCopyApproved
                            └🟩 Read Model: 可用文案清單
🟥 H: 多平台自動發佈 → Phase4+，MVP 僅產出供人工貼上
```

**要點**：文案/標題錯了影響小（無錯價風險），是當天有感的破冰點。無需先建客戶/物件庫——**零輸入**。

---

## 3. 流程：帶看說帖生成（Phase 1 · 零延遲靜態資料）

```
🟡 經紀人
  └🔵 請求帶看說帖 (物件地址/區域)
      └[治理閘: tenant scope, 風險=低]
        └🟫 BriefingSession
            ├🩷 twtools (捷運線/行政區/學區 — 即時靜態資料)
            └🟠 帶看說帖已生成  ViewingBriefingGenerated
                └🟪 Policy: 含外部地理資料 → 附資料來源標註
                    └🟩 Read Model: 說帖卡 (機能/交通/學區)
🟥 H: 嫌惡設施/學區劃分易過時 → 標來源 + 不保證即時
```

**要點**：捷運/行政區是即時靜態資料，**無 lvr 季度延遲問題**，無錯價風險。

---

## 4. 流程：結構化客戶記憶（Phase 2 · ★Core Domain · 護城河）

```
🟡 經紀人
  └🔵 用 LINE 語音/訊息描述客戶 ("林先生 想找信義區 3房 預算1500-2000萬")
      └🩷 STT (Groq whisper-large-v3-turbo) — 語音轉文字
        └[治理閘: tenant+seat scope, 含 PII → 風險=高]
          └🟫 Customer (PII 邊界)
              └🟠 客戶需求草稿已擷取  CustomerRequirementDrafted
                  └🟪 Policy: 含 PII → 強制 HITL 確認 (不可自動建檔)
                      └🔵 經紀人確認建檔
                          ├🟠 客戶已建檔  CustomerProfiled
                          ├🟠 客戶記憶已寫入  CustomerMemoryWritten
                          │    └🩷 mem0 MCP [namespace = tenant_id:seat_id:customer_id]
                          │    └🟥 H7: 隔離未就緒前此步禁用
                          └🟪 Policy: 客戶建檔後 → 產生跟進任務
                              └🟠 跟進任務已建立  FollowUpTaskScheduled
                                  └🟪 Policy: 任務到期 → Cron 主動推播
                                      └🩷 Cron scheduler
                                        └🟠 跟進提醒已推播  FollowUpReminderPushed
                                            └🩷 LINE Push API (額度監控)
```

**要點**：這是「第二大腦」名實相符的核心，也是切換成本來源。**主動提醒是 Agent 與 Bot 的分水嶺**。結構化（非 Markdown）才能做到「預算 AND 區域 AND 房型」精準比對。

---

## 5. 流程：結構化配對（Phase 2 · ★Core Domain）

```
🟡 經紀人 ─🔵 確認物件檔案 ─🟫 Listing ─🟠 物件已建檔 ListingProfiled
                                          (下架 ─🟠 ListingDelisted)
🟪 Policy: whenever ListingProfiled OR CustomerRequirementUpdated → 觸發配對掃描
  └🔵 執行配對 (系統內部 command)
      └[治理閘: 硬約束 WHERE tenant_id=? — 配對不可跨租戶]
        └ MatchingService (Domain Service，非 Aggregate)
            ├ SQL WHERE: 預算區間 ∩ 區域 ∩ 房型 ∩ 條件
            └🟠 配對候選已產生  MatchCandidatesProduced
                └🟩 Read Model: 配對候選清單 (可解釋, 標明命中條件)
                    └🟪 Policy: 候選產生 → 通知經紀人 (非自動通知客戶)
                        └🔵 經紀人核准後 → 🟠 MatchPresented → 對外溝通 (HITL)
🟥 H: MVP 用 SQL WHERE (可解釋/無外送); embedding 配對待合規後再上
```

**要點**：MVP 用 **SQL WHERE 結構化配對**（可解釋、無資料外送），合規前不上 embedding。

---

## 6. 流程：行情輔助（Phase 3 · 降級 · 重錯價防護）

```
🟡 經紀人
  └🔵 查詢行情 (地址/區域)
      └[治理閘: 風險=高 → 啟動錯價防護鏈]
        └🟫 MarketCompQuery
            ├🩷 lvr-trades MCP (ACL 包裝)
            ├🟪 Policy: TimestampGuard — 過濾 <2010 或 >今日+90天 的列 (濾 2101/2033/1921)
            ├🟪 Policy: 地址比對失敗 → 拒答 (不猜)
            ├🟪 Policy: 單價雙重檢核 (總價/坪數 vs 單價欄位)
            ├🟪 Policy: 信心分數 < 閾值 → 拒答或 HITL
            └ 分支:
               ├🟠 行情參考已產出  MarketCompProvided (附「資料更新至 YYYY-MM」+ 信心分數 + 預售/成屋/車位標註)
               └🟠 行情查詢已拒答  MarketCompRefused (寧可不答)
🟥 H3/H4: 任何未加上界防呆的「最新行情」查詢都會回傳 2101 垃圾值 → 錯價地雷
```

**要點**：話術改「**近 N 季官方彙整 + 趨勢**」，非「即時」。**拒答優於猜測**。錯一次永久棄用。

---

## 7. Cross-cutting：治理與稽核（Phase 0 · 貫穿全部流程）

```
🟪 Policy (全域前置): 任何 Command → 注入 (tenant_id, seat_id) scope, 無 scope 即拒絕
🟪 Policy (全域前置): 任何資料存取 → 強制 WHERE tenant_id=? (Inv-1)
🟪 Policy (全域後置): 任何對外訊息/寫入 → 必過 HITL gate (Inv-2)
🟪 Policy (全域旁路): 每個 Command/Event → append-only 稽核
  └🟠 稽核軌跡已記錄  AuditTrailRecorded
🟡 經紀人
  └🔵 回報 AI 報錯價/錯資訊
      └🟠 錯價已回報  MispricingReported
          └🟪 Policy: 北極星反指標 +1 → 觸發停損檢討 (功能級)
```

---

## 8. 事件流彙整（依 Bounded Context）

| Context | Command(🔵) | Aggregate(🟫) | Domain Event(🟠) | Policy(🟪) |
|---|---|---|---|---|
| Content Generation | 提交物件資訊 / 核准文案 / 請求說帖 | CopywritingSession, BriefingSession | ListingCopyGenerated, ListingCopyApproved, ViewingBriefingGenerated | 生成後→HITL；說帖→附來源 |
| Customer & CRM | 描述客戶 / 確認建檔 / 請求刪除 | Customer, Requirement | CustomerRequirementDrafted, CustomerProfiled, CustomerMemoryWritten, CustomerErasure* | PII→強制HITL；建檔→產生跟進 |
| Listing Lifecycle | 確認物件檔案 / 下架 | Listing | ListingProfiled, ListingDelisted | 建檔→觸發配對掃描 |
| Matching | 執行配對 | —（Domain Service: MatchingService；候選為 Read Model） | MatchCandidatesProduced, MatchPresented | ListingProfiled/需求更新→掃描；候選→通知經紀人 |
| Interaction & Scheduling | （由 Policy 觸發） | FollowUpTask | FollowUpTaskScheduled, InteractionLogged | 任務到期→C9 推播 |
| Notification (C9) | （由 Policy 觸發） | — | FollowUpReminderPushed | 到期推播；冪等（Inv-9） |
| Market Intelligence | 查詢行情 | MarketCompQuery | MarketCompProvided, MarketCompRefused | TimestampGuard；比對失敗→拒答 |
| Governance | 回報錯價 | AuditTrail, ErrorReport | AuditTrailRecorded, MispricingReported, HITLApproved, HITLRejected | scope注入；HITL；反指標停損 |

完整事件目錄與 payload 見 [`domain-events.md`](domain-events.md)；聚合定義見 [`aggregates.md`](aggregates.md)。
