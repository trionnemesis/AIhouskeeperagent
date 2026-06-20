# Traceability — CR:2026:007 GKE 部署

```
DEPLOY:GKE:GATEWAY（Envoy egress proxy + egress default-deny）
  ├─ Invariant : DI-1(PII egress), DI-4(591/leju + 不可繞過), DI-7
  ├─ Spec      : platform-architecture.md §AI Gateway / §不變量→GKE 強制
  ├─ Verify(P3): conftest(egress default-deny/唯一出口) + kind smoke(直連失敗/經閘通)
  └─ Telemetry : ⏳ egress 拒絕數 / filter 延遲

DEPLOY:GKE:TOPOLOGY（namespace-per-tenant）
  ├─ Invariant : Inv-1(租戶隔離 P0)
  ├─ Spec      : platform-architecture.md §Namespace 模型 / §工作負載
  ├─ Verify(P3): conftest(跨租戶零連通) + dual-tenant CI(SEC-1)
  └─ Telemetry : ⏳ 每租戶資源用量

DEPLOY:GKE:NETSEC（私有叢集/NAT/Cloud Armor/WI+Secret Manager/Pod 安全）
  ├─ NFR       : SEC-2/4/5, OPS-1(pin/禁 latest)
  ├─ Spec      : platform-architecture.md §網路與安全
  ├─ Verify(P3): conftest(no latest/runAsNonRoot) + secret 掃描 + 偽簽章 401
  └─ Telemetry : ⏳ WAF 攔截 / 憑證輪替

DEPLOY:GKE:STATE（Cloud SQL + Memorystore）→ spawns CR-2026-008
  ├─ Invariant : Inv-3(audit append-only), Inv-7(mem0 gating), DI-7
  ├─ Spec      : data-and-cicd.md §狀態服務 / §data MCP 遷移
  ├─ Verify(P3): audit REVOKE 改寫失敗；data MCP smoke（遷 Postgres 後行為不變）
  └─ Telemetry : ⏳ 連線數 / 快取命中

DEPLOY:GKE:CICD（Artifact Registry + Cloud Build + Config Sync + Kustomize）
  ├─ NFR       : OPS-1/3；Gate B 閘
  ├─ Spec      : data-and-cicd.md §IaC / §CI-CD
  ├─ Verify(P3): kubeconform/conftest gate；@gateB 綠才 sync prod
  └─ Telemetry : ⏳ 發版/回滾次數

DEPLOY:GKE:OBS（Managed Prometheus / Logging / Trace / 北極星）
  ├─ NFR       : OBS-1/2/3/4, COST-3
  ├─ Spec      : data-and-cicd.md §可觀測性
  └─ Telemetry : ⏳ 北極星=錯價回報數
```

> 對應既有：[02-spec/system-architecture](../../../02-spec/system-architecture.md)（邏輯架構不變）、[05-data-mcp/gateway-compliance](../../../05-data-mcp/gateway-compliance.md)（5 WASM filter → proxy-wasm 落地）、[04-roadmap/deployment](../../../04-roadmap/deployment.md)（部署步驟基底）。
