# 實作 Repo 佈局（Node.js Monorepo）

> 本 spec kit 是規格；本檔給出**實作 repo** 的目錄骨架，讓工程師知道哪個 package 對應哪個 context/MCP。spec-kit 本身（spec 文件）可作為實作 repo 的 `spec/` 子目錄。

```
hermes-real-estate/
├─ spec/                      # ← 本 spec-kit 內容（spec/DDD/BDD/roadmap）
├─ package.json               # workspaces monorepo
├─ packages/
│  ├─ gateway/                # Node Tenant Edge Gateway：webhook 終結/驗章/dedup/路由
│  ├─ governance/             # GovernanceGate / TenantScopeResolver / HITL / audit
│  ├─ acl/                    # Mem0Acl / lvr ACL（外部源防腐層）
│  ├─ db/                     # Drizzle/Kysely schema（erm.dbml 對映）+ scope-helper + migrations
│  ├─ mcp-content/            # content-gen-mcp        (C4)
│  ├─ mcp-crm/                # customer-crm-mcp       (C5, ★Core)
│  ├─ mcp-matching/           # matching-mcp           (C6, ★Core)
│  ├─ mcp-market/             # market-comp-mcp        (C8, ACL+防護)
│  └─ mcp-notify/             # notify-mcp / cron 接線 (C9)
├─ shared/
│  ├─ scope-helper/           # 強制 WHERE tenant_id 的 typed query builder（禁裸 SQL）
│  └─ tw-utils/               # 自建 deterministic 台灣工具（統編 checksum/中英地址/郵遞區號/捷運），重實作 twtools；不連 hosted
├─ test/
│  └─ features/steps/         # BDD step definitions（對映 spec/03-features）
├─ infra/
│  └─ hermes/                 # Hermes pinned commit 部署設定（per-tenant home）
└─ .github/workflows/
   └─ bdd-gate-b.yml          # Gate B required check
```

## package ↔ context 對照

| package | Bounded Context | 關鍵不變量 |
|---|---|---|
| `gateway` | C1 邊界 | Inv-1（scope 注入）、Inv-9（dedup） |
| `governance` | C2 | Inv-1/2/3/8 |
| `acl` | C5→mem0 / C8→lvr | Inv-4/7、REL-4 |
| `db` + `shared/scope-helper` | 全 | Inv-1（資料層強制） |
| `mcp-*` | C4/C5/C6/C8/C9 | 各 context |

## 關鍵約束

- **`shared/scope-helper`** 是唯一資料存取入口，typed query builder 在 compile-time 要求 `ctx.tenantId`，**禁止裸 SQL 繞過**（落地 Inv-1）。
- `acl` 是 mem0/lvr 的唯一出口，强制 namespace（Inv-7）與 TimestampGuard（Inv-4）。
- Hermes 不在 monorepo 內被改；以 `infra/hermes` pinned commit 部署，僅透過 MCP/API 整合（OPS-1）。
