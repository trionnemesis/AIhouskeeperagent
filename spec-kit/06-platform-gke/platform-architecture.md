# GKE 平台架構

> Autopilot + 私有叢集 + Cloud NAT；Envoy egress gateway 為唯一不可繞過出口；namespace-per-tenant 隔離。

## 叢集

| 項 | 值 | 理由 |
|---|---|---|
| 模式 | **GKE Autopilot** | 最少 ops、per-pod 計費、節點安全預設強（runAsNonRoot、無特權） |
| 私有性 | **私有叢集**（私有節點、無公開節點 IP） | 節點不可從外網直達；出向經 Cloud NAT |
| 出向 | **Cloud NAT**（集中受控） | 唯一對外路徑；配合 NetworkPolicy 收斂至 Gateway |
| 控制面 | 授權網路限制 | kube-API 僅限維運網段/Cloud Build |
| 區域 | 單一 region 多 zone（如 `asia-east1`） | 低延遲、HA；資料落地境內考量 |

## Namespace 模型（namespace-per-tenant）

```
cluster
├─ ns: tenant-<id>          每租戶一份（部署隔離；綁單一 TENANT_ID, Inv-1）
│   ├─ FastAPI Edge (Deployment+HPA)      LINE webhook HMAC 終結 (SEC-4)
│   ├─ Hermes runtime (StatefulSet+PVC)   per-tenant HERMES_HOME；image 鎖 HERMES_PINNED_TAG
│   ├─ Node domain MCP C4/C5/C6/C8/C9     C5 customer-crm = mem0 唯一路徑(Mem0Acl, Inv-7)
│   └─ (mem0 client：MEM0_ENABLED=false 至 Gate B)
│   · RBAC + ResourceQuota + NetworkPolicy（跨租戶 ns 零連通）
├─ ns: data-mcp            共用（公開參考資料，非 tenant-scoped）
│   ├─ lvr / public-safety / amenities / company-registry (Deployment+HPA, stateless_http)
│   └─ ETL CronJob（plvr 1/11/21、犯罪/事故；走 govnet 安全 fetcher）
├─ ns: gateway            共用
│   ├─ Envoy egress gateway (Deployment+HPA, proxy-wasm 5 filter)  ← 不可繞過
│   └─ GKE Gateway API + Cloud Armor（LINE webhook 入口，managed TLS）
└─ ns: platform           共用（Managed Prometheus、OTel collector、External Secrets、Cloud SQL Auth Proxy）
```

> data MCP 放共用 ns（持公開 gov 資料、無租戶 PII）；租戶 scope 由 Gateway 的 ToolAuthZ Bearer + RAG Adapter 強制（[gateway-compliance](../05-data-mcp/gateway-compliance.md)），非靠 data MCP 自身。

## 工作負載對照

| 工作負載 | kind | 儲存 | 擴縮 |
|---|---|---|---|
| FastAPI Edge | Deployment | — | HPA（CPU/RPS） |
| Hermes runtime | StatefulSet | PVC（per-tenant home, RWO） | 單副本/租戶（home 有狀態） |
| Node domain MCP | Deployment | — | HPA |
| Python data MCP | Deployment | —（狀態移 Cloud SQL） | HPA（stateless_http=True） |
| Envoy egress gateway | Deployment | — | HPA（egress 量） |
| ETL | **CronJob** | — | `0 6 1,11,21 * *` 等 |

## AI Gateway：Envoy egress proxy（唯一不可繞過閘）

```
app pod (Hermes/MCP/FastAPI)
   │  NetworkPolicy: egress default-deny；唯一放行 = gateway ns 的 Envoy
   ▼
Envoy egress gateway  ── proxy-wasm 鏈：[Policy][PII][Router][ToolAuthZ][RAG] ──▶ Cloud NAT ──▶ 外部來源
   ▲ Bearer(ToolAuthZ 簽發) + mTLS                                              （gov 白名單；591/leju 封鎖）
```

- **5 個 WASM filter** = [gateway-compliance.md](../05-data-mcp/gateway-compliance.md) 規格的 proxy-wasm 落地（職責不變）。
- **不可繞過保證**（落地對應 gateway-compliance「網路強制」表）：
  1. NetworkPolicy **egress default-deny**；app pod 唯一允許的出向目的地 = Envoy gateway Service。
  2. 直連封鎖：data MCP 僅接受來自 gateway 的連線（NetworkPolicy ingress 限定 + mTLS/Bearer）。
  3. 591/leju 域名於 Envoy filter + Cloud NAT 規則雙重封鎖（DI-4）。
  4. 對外 internet 出向僅 Envoy pod 可達 Cloud NAT（其餘 pod egress 不含 0.0.0.0/0）。

## 網路與安全

| 控制 | GKE 手段 |
|---|---|
| 入口 WAF/限流 | **Cloud Armor** 附於 GKE Gateway API；LINE webhook → FastAPI |
| TLS（入口） | Google-managed cert |
| Secret | **Secret Manager + Workload Identity**（CSI driver / External Secrets）；零入版控 |
| Pod 安全 | Autopilot 強制 runAsNonRoot/no-privileged；補 readOnlyRootFilesystem、drop ALL caps、seccomp RuntimeDefault |
| image 來源 | **Artifact Registry**；禁 `:latest`（Hermes 鎖 tag, OPS-1）；Binary Authorization（簽章驗證，選配） |
| 跨租戶隔離 | NetworkPolicy：tenant-<a> ns ↔ tenant-<b> ns 零連通；各 ns ResourceQuota/LimitRange |

## 不變量 → GKE 強制（驗收綁定）

| 約束 | GKE 落地 | 驗證（Phase 3） |
|---|---|---|
| Inv-1 租戶隔離(P0) | namespace + NetworkPolicy + per-tenant DB；查詢仍 `WHERE tenant_id` | conftest：跨租戶 ns 無 allow；dual-tenant CI |
| DI-4 不可繞過 egress / 591·leju | egress default-deny + 唯一 Envoy 出口 + 域名封鎖 | kind smoke：app pod 直連 591 失敗、經 gateway 才通 |
| DI-1 PII egress 遮罩 | PII WASM 於 Envoy egress（寫 mem0 前 hook） | 輸出無門牌/自然人；mem0 落地前過濾 |
| DI-5 治安粒度 | data MCP tool 既有護欄（[CR-006](../../05-data-mcp/changes/CR-2026-006-pubsafe-complete/gates.md)） | 既有 smoke 於叢集內重跑 |
| SEC-3 audit append-only | Cloud SQL role `REVOKE UPDATE,DELETE` | 嘗試改 audit 失敗 |
| SEC-4/5 webhook 驗章/allowlist | FastAPI（Cloud Armor 前置） | 偽簽章 401 |
| OPS-1 Hermes pin | image tag 固定、禁 latest | conftest：no `:latest` |
