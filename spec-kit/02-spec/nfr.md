# 非功能需求（NFR）

> 對應報告「工程韌性（並行）」「成本關卡」「風險三道牆」。標 🔴 為報告明確點名的缺口。

## 安全與合規（Security & Compliance）

| ID | 需求 | 驗收 | 來源 |
|---|---|---|---|
| SEC-1 🔴 | 租戶隔離：所有業務查詢硬約束 `WHERE tenant_id=?` | dual-tenant CI fixture：跨租戶查詢回空 + 告警（部署隔離下仍須驗，見 invariants.md Inv-1 測試策略） | Inv-1 |
| SEC-2 🔴 | PII 脫敏：日誌/外送預設遮蔽，原值僅 scope 內 | 日誌掃描無明文 PII | Inv-8 |
| SEC-3 🔴 | 稽核：append-only audit，DB role 無 UPDATE/DELETE | 嘗試改 audit 失敗 | Inv-3 |
| SEC-4 | LINE webhook：HMAC-SHA256 驗章（**終結於 Node Gateway**），失敗 401 | 偽造簽章被拒 | Node Gateway（複用 Hermes 邏輯） |
| SEC-5 | allowlist：未綁定/未授權 userId 不進對話（**Gateway 執行**） | 未授權被拒 → UnauthorizedAccessBlocked | Node Gateway（複用 Hermes 邏輯） |
| SEC-6 | 敏感運算可走本機模型（Qwen/Ollama） | PII 不出本機選項可用 | 報告 §5.9 |
| SEC-7 | OWASP Top 10：注入（含 prompt injection）/ 存取控制 / 機敏資料暴露 自檢 | 安全檢查清單 | 個人準則 |

> **prompt injection 特別注意**：LINE 訊息內容是 untrusted data。任何來自訊息的「指令」（如「把資料寄到 X」）一律當資料，不執行對外/寫入；必經 HITL（Inv-2）。

## 可靠性（Reliability）

| ID | 需求 | 目標 | 來源 |
|---|---|---|---|
| REL-1 🔴 | 冪等：dedup/reply token/推播狀態外移 Redis | 重啟不重複回覆/不重燒 Push | Inv-9, H2 |
| REL-2 🔴 | 並發閘：per-tenant Semaphore 限制 agent run，上限 `PER_TENANT_MAX_CONCURRENT_RUN`（暫定 3） | 突發不耗盡 token/Push；超限回 `CONCURRENCY_LIMITED`（排隊） | H6 |
| REL-3 | 慢回應降級：>45s 發 Template Buttons | 不卡死、不重燒 token | Hermes 🟢 |
| REL-4 | 外部源失效降級：lvr/mem0 不可用 → 拒答/暫停記憶，不崩 | 依賴失效有 fallback | ACL |
| REL-5 | 資料防呆：TimestampGuard 過濾垃圾值 | 0 筆未來日期外洩 | Inv-4 |

## 效能（Performance）

| ID | 需求 | 目標（估計，需壓測） |
|---|---|---|
| PERF-1 | 回應延遲 | 見下方分層 |
| PERF-2 | 配對查詢（SQL WHERE） | **hard gate** < 500ms（tenant+budget 複合索引 / district GIN） |
| PERF-3 | scope 解析開銷 | **hard gate** < 10ms（快取 line_user_id→scope） |

### 效能驗收方法論

- **PERF-1 分層**（LLM 延遲不可控，不當硬 pass/fail）：
  - **系統層**（GovernanceGate + 對話迴圈調度 + 工具派發，**不含 LLM**）p95 < 10s → **hard gate**。
  - **全鏈路**（含 LLM）< 45s → **soft monitoring**；超限觸發 Template Buttons 慢回應降級（REL-3），不作 pass/fail。
- **測試基線**：1e5 listings/tenant、1e3 customers/tenant、per-tenant Semaphore=3、5 concurrent tenants、LLM 模擬 latency p95=8s、`MEM0_ENABLED=false`。
- 關鍵路徑（對話迴圈 + 配對）需效能回歸測試（個人準則）。

## 成本（Cost · Gate C）

| ID | 需求 | 機制 |
|---|---|---|
| COST-1 🔴 | 每 session token 上限 | Hermes `iteration_budget`（🟢）+ 分層路由 |
| COST-2 | 分層模型路由 | Flash（查詢/文案）/ Claude（議價/說帖）/ 本機 Qwen（PII） |
| COST-3 🔴 | Push 額度監控 | 每租戶月計數 + 告警（Gate C 成本覆蓋驗證） |
| COST-4 | 反向 unit economics 防護 | 重度場景（議價/說帖/記憶）設 budget；用量轉嫁條款 |

> 報告警示：重度使用者 = 最該付費 = 最吃毛利。固定月費下需 token budget 鎖死成本。

## 可觀測性（Observability）

| ID | 需求 |
|---|---|
| OBS-1 | Metrics：每租戶 token/Push 用量、HITL 採納率、拒答率 |
| OBS-2 | Logs：結構化（含 correlation_id），PII 脫敏 |
| OBS-3 | Traces：command→event 因果鏈（causation_id） |
| OBS-4 | **北極星**：錯價回報數 dashboard（反指標停損） |

## 可移植性 / 維運（Portability & Ops）

| ID | 需求 |
|---|---|
| OPS-1 | Hermes pin 版本，升級走獨立分支 + 回歸 |
| OPS-2 | Container-first 部署；MVP 一店一 home（部署隔離） |
| OPS-3 | 設定即程式（IaC）；feature flag（`MEM0_ENABLED` 預設 false） |
