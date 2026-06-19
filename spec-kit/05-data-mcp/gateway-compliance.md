# AI Gateway 合規層規格（PII / ToolAuthZ / Policy WASM）

> 唯一**不可繞過**的最終閘。本檔規格化資料層相關的三個 WASM 插件（PII / ToolAuthZ / Policy），對接 [`invariants.md`](invariants.md) DI 系列。Router / RAG Adapter 列為相鄰但本輪輕描述。

## 為什麼合規必在 Gateway（非 MCP middleware）

FastMCP middleware 是**私有概念**：換 client、直連 MCP、或繞過 client 即失效。**權威合規邊界必在 Gateway egress**，並由網路層強制所有出向流量經 Gateway（block 直連 provider egress），否則 egress 閘可被繞過。

```
agent ⇄ Gateway(WASM 鏈) ⇄ MCP server ⇄ 來源
              ▲ 不可繞過          ▲ middleware 僅輔助(rate-limit/cache)
```

---

## PII 插件（DI-1，最高優先）

**觸發點（關鍵）**：須在 **MCP post-tool 回傳 / 寫入 mem0 之前** hook，**非僅** LLM input/output hook——因為若只在 LLM I/O 遮罩，原始 PII 已落 mem0。

**規範**：
- 來源**未脫敏假設**：實價登錄 2.0 門牌/地號完整揭露（R1），任何來自 `lvr-mcp` 的回傳一律當含 PII 處理。
- **遮罩對象**：門牌號、地號、自然人姓名、可反查自然人之識別、聯絡資訊。**法人統編保留**。
- **遮罩策略**：對外輸出脫敏（如「信義區 OO 路 ***」）；原值僅在 tenant scope 內、且經稽核後存取（延續主 spec Inv-8）。
- **落地前置**：provenance 標記後，PII 過濾通過才入 mem0（DI-7）。

```
MCP tool result → [PII hook]：
  detect(門牌/地號/姓名/電話/統編→自然人)
  → redact(對外) / scope-bind(原值)
  → 通過 → 入 mem0 / 回 agent
  → 命中 → PiiAccessLogged（主 spec C2 稽核）
```

---

## ToolAuthZ 插件（DI-4，來源黑名單）

**規範**：
- **角色 × tool 授權**：依 Bearer 帶的角色/租戶 scope 決定可呼叫哪些 MCP tool。
- **來源黑名單（硬性）**：`591`、`leju` 及任何「ToS 禁止 + 有技術保護措施」之來源 → **預設禁用**。
  - **放行條件**：法務意見書 + B2B 授權證明，且在 Gateway 設定明確 allowlist 條目。
  - 依據：公平會公處字第106084號裁罰先例、刑法§358/§359、各站 ToS（R3）。
  - **robots.txt 不構成放行依據**；以 ToS / 公平法見解為準。
- **配額閘**：對 GCIS（每日次數/連線上限）、TDX（速率/收費層）在 Gateway 做租戶級配額管控（與 MCP middleware 的站台級 rate-limit 互補）。

```
agent tool call → [ToolAuthZ]：
  role 可呼叫此 tool? → no → SCOPE_* 拒絕
  source ∈ 黑名單(591/leju)? → 無法務 allowlist → 拒絕 + 稽核
  租戶級並發足? → no → CONCURRENCY_LIMITED（REL-2，並發閘）
  來源級每日配額足(GCIS/TDX)? → no → SOURCE_QUOTA_EXCEEDED（DI-8，外部源上限）
  → 放行
```

---

## Policy 插件（DI-2/DI-3/DI-5，跨 tool 統一策略）

**規範**（egress 對所有資料 tool 輸出統一施加）：
- **來源顯名**（DI-2）：政府源輸出標來源機關；OSM 標 ODbL 署名。未顯名 → 攔截/補標。
- **資料時點 + 免責**（DI-3）：行情輸出附 `data_as_of` + 申報遲延警示；禁「即時」字樣。
- **治安中性化**（DI-5）：禁門牌/點位級精準呈現、禁「高犯罪/治安差/嫌惡」等負面標籤；區域統計禁套單一物件。
- **嫌惡設施中性用語**：附來源 + 時點，不下房價影響結論。

---

## Router / RAG Adapter（相鄰，本輪輕描述）

- **Router**：多源 fallback（如 lvr 失效 → 標 source_unavailable 降級；geocoding TGOS→NLSC）。
- **RAG Adapter**：檢索結果過濾刊登者/自然人個資，標 provenance 與來源權威度（政府 > 官方 API > 爬蟲）。

---

## 網路強制（不可繞過保證）

| 控制 | 規範 |
|---|---|
| egress 集中 | 所有 MCP server 與 agent 的出向流量強制經 Gateway；防火牆 block 直連 provider/API/外網 |
| 直連封鎖 | MCP server 不得被 agent 以非 Gateway 路徑直呼（網段隔離 + mTLS/Bearer） |
| 黑名單域名 | 591/leju 域名於出向層封鎖，與 ToolAuthZ 黑名單雙重保險 |

## 驗收

見 [`features/gateway-pii-egress.feature`](features/gateway-pii-egress.feature) + [`features/gateway-toolauthz-blacklist.feature`](features/gateway-toolauthz-blacklist.feature) + [`features/gateway-policy-disclosure.feature`](features/gateway-policy-disclosure.feature)。
