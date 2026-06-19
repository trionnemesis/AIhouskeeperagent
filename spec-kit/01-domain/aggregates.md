# 聚合 / 實體 / 值物件 / 領域服務

> DDD Tactical Design。每個 Aggregate 是一致性與交易邊界；**每個業務 Aggregate 都帶 `tenant_id`，且不變量 Inv-1 強制 scope**。

## 聚合根速覽

| Aggregate Root | Context | 一致性邊界內含 | 關鍵不變量 |
|---|---|---|---|
| `Tenant` | C1 | Branch[], Seat[] | tenant 為隔離最外層；刪除為軟刪除 |
| `Seat`（經紀人） | C1 | Identity（LINE 綁定） | 一 Seat 屬唯一 Branch/Tenant；allowlist 控管 |
| `Customer`（客戶） | C5 | Requirement[], PII 欄位 | **PII 邊界**；含 PII 的變更必經 HITL |
| `Listing`（物件） | **C-Listing**（owning） | Attribute[], 文案 ref, status | 隸屬唯一 tenant；狀態機 Open→Reserved/Closed/Delisted；**C4/C6 以 `listing_ref` 參照、不共享聚合** |
| `CopywritingSession` | C4 | ListingCopy 草稿/核准態 | 未核准草稿不外流 |
| `BriefingSession` | C4 | 說帖內容 + 來源標註 | 外部地理資料必附來源（Inv-6a） |
| `FollowUpTask` | C7（推播事件屬 C9） | 到期時間、狀態 | 到期觸發推播；推播冪等（Inv-9） |
| `MarketCompQuery` | C8 | 查詢條件、結果、信心分數 | **TimestampGuard 通過才產出**；否則 Refused |
| `AuditTrail` | C2 | append-only 記錄 | 不可變更/刪除 |
| `ErrorReport` | C2 | 錯價/錯資訊回報 | 觸發北極星反指標 |
| `HITLApproval` | C2 | 待核准項、決議 | 對外/寫入動作的放行閘 |

---

## 核心聚合詳述

### `Customer`（C5 · ★Core · PII 邊界）

```
Customer (root)
├─ id: CustomerId            (tenant-scoped)
├─ tenant_id: TenantId       ← 隔離錨點 (NOT NULL)
├─ owner_seat_id: SeatId     ← 歸戶
├─ profile: CustomerProfile  (VO: 稱謂/聯絡方式[PII]/標籤)
├─ requirements: Requirement[]   ← 子實體
├─ memory_ref: MemoryRef     (VO: 指向 mem0 namespace, 非內嵌)
└─ status: Active | Archived

不變量:
- Inv-1: 任何讀寫硬約束 tenant_id
- Inv-2: profile 中 PII 欄位的建立/變更 → 必經 HITL
- Inv-7: memory_ref.namespace 必須 = `${tenant_id}:${owner_seat_id}:${id}`
```

#### `Requirement`（Customer 聚合內子 Entity — 配對的關鍵）

```
Requirement (子 Entity，有 identity，可變更)
├─ id: RequirementId               (有 identity → Entity 而非 VO)
├─ budget_min, budget_max: Money   (結構化，非自由文字)
├─ districts: District[]            (行政區，受控詞彙)
├─ room_layout: RoomLayout         (e.g. 3房2廳)
├─ must_have / nice_to_have: Condition[]
└─ priority: int

身分: Requirement 為 Entity（有 RequirementId、可被 CustomerRequirementUpdated 以 diff 變更），非 VO。
理由: 非結構化 Markdown 做不到「預算 1500-2000萬 AND 信義區 AND 3房」精準比對。
```

### `MarketCompQuery`（C8 · 重防護）

```
MarketCompQuery (root)
├─ query: { address?, district, building_type }
├─ raw_rows: Trade[]        (來自 lvr ACL)
├─ guarded_rows: Trade[]    (TimestampGuard + 單價檢核 後)
├─ confidence: ConfidenceScore
├─ data_as_of: YearMonth    (「資料更新至 YYYY-MM」)
└─ outcome: Provided(comps, disclaimer) | Refused(reason)

不變量:
- Inv-4: guarded_rows 必須排除 trade_date <2010 或 >今日+90天
- Inv-5: 地址比對失敗 OR confidence<閾值 → outcome = Refused
- Inv-6: Provided 必附 data_as_of + 預售/成屋/車位標註
```

### `HITLApproval`（C2 · 治理閘）

```
HITLApproval (root)
├─ subject_ref: 指向待核准的 Command/草稿 (文案/客戶建檔/對外訊息)
├─ risk_level: Low | High
├─ proposed_payload: 草稿內容
├─ decision: Pending | Approved(by, at) | Rejected(by, at, reason)
└─ audit_ref: AuditTrailId

不變量:
- Inv-2: risk=High 或「對外/寫入」類動作，decision≠Approved 前不得執行
- Inv-3: 每個 decision 產生 append-only AuditTrail
- 逾時: Pending 逾 72h 自動 Rejected（reason=approval_timeout）
```

> **狀態機**：`HITLApproval`、`MarketCompQuery`、`FollowUpTask`、`Listing`（Open→Reserved/Closed/Delisted）的完整轉移圖、終態與逾時行為見 [`../02-spec/governance-state-machines.md`](../02-spec/governance-state-machines.md)。`Listing` 由 **C-Listing** 單一 owning context 擁有完整生命週期事件（`ListingProfiled`/`ListingDelisted`），C4/C6 僅以 `listing_ref` 參照與 read model 消費。

---

## 領域服務（Domain Services）

| Service | Context | 職責 | 為何是 Service（非 Aggregate 方法） |
|---|---|---|---|
| `MatchingService` | C6 | 跨 Customer×Listing 配對 | 涉及多個聚合，無單一所有者 |
| `TenantScopeResolver` | C1 | 從 LINE userId 解析 (tenant, seat) | 跨 Identity/Tenancy |
| `GovernanceGate` | C2 | scope 注入 → 風險判定 → HITL 路由 → audit | 橫切，無歸屬單一聚合 |
| `MispricingGuard` | C8 | TimestampGuard + 單價檢核 + 信心評分 | 純策略集合 |

---

## 值物件（Value Objects，部分）

`TenantId` · `SeatId` · `CustomerId` · `Money`（幣別+金額）· `District`（受控詞彙）· `RoomLayout` · `YearMonth` · `ConfidenceScore`（0–1 + 等級）· `MemoryRef`（mem0 namespace 指標）· `PiiField`（值 + 脫敏遮罩 + 分類標籤）。

> VO 不可變（immutable）；`PiiField` 在序列化到日誌/外部時**預設輸出脫敏遮罩**，原值僅在 tenant scope 內存取。
