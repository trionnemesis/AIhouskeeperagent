# 部署步驟（MVP · 一店部署隔離）

> 對應架構「部署隔離（一店一 home）」與 OPS-2。一租戶 = 一組 Hermes home + 一組 Node.js 服務（綁單一 `TENANT_ID`）。

## 前置

- 設定見 [`../02-spec/configuration.md`](../02-spec/configuration.md)（secret 經密管注入，不入版控）。
- `MEM0_ENABLED=false`（Gate B 通過前不得開）。

## 逐步

1. **環境**：建立隔離環境（container/VM），設 `TENANT_ID`、`HERMES_HOME=/srv/hermes/<tenant>`。
2. **資料層**：
   - 起 Postgres + Redis。
   - 跑 DB migration（Drizzle，由 `erm.dbml` 衍生）。
   - **audit_logs 套用 append-only**：`REVOKE UPDATE, DELETE ON audit_logs FROM app_role;`（或 BEFORE UPDATE/DELETE 觸發器 RAISE，落地 SEC-3/Inv-3）。
3. **Hermes bootstrap**：以 `HERMES_PINNED_TAG` 檢出（不跟 main），啟動 per-tenant home；**停用 Hermes 內建 LINE webhook 入口**，僅保留 reply/push 出口。
4. **Node 服務**：啟動 `gateway` + `governance` + `mcp-*`，全部綁定 `TENANT_ID`；向 Hermes 註冊 domain MCP servers。
5. **LINE 接線**：
   - named tunnel（cloudflared/ngrok）+ TLS 對外曝 `gateway` 的 `/line/webhook`。
   - LINE Developer Console 設 webhook URL → **Node Gateway**（非 Hermes:8646）。
   - Gateway 持有 `LINE_CHANNEL_SECRET` 做 HMAC 驗章。
6. **健康檢查順序**：Postgres → Redis → Hermes runtime → domain MCP → gateway readiness（任一未就緒不對外）。
7. **Gate B 驗證**：CI `bdd-gate-b.yml` 的 `@gateB` 全綠 → 才允許接真實客戶資料；通過後可評估開 `MEM0_ENABLED`。

## 升級 / 維運

- Hermes 升級：獨立分支檢出新 tag → 跑 LINE 協定回歸 + 本 spec BDD → 綠燈才換版（OPS-1）。
- 監控：每租戶 token/Push 用量（COST-3/OBS-1，來源 `outbound_messages`）、錯價回報數（北極星）、p95（PERF）。
- 規模化（轉 `MULTITENANCY_MODE=app_level`）：見架構文件「部署隔離 vs 應用層多租戶」對照表。
