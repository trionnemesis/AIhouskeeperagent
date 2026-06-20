# ADR-001：MVP 改用單 VM 部署（GKE 留作規模化目標）

> 狀態：**Accepted**（2026-06-20，使用者拍板「修正方向改為使用 VM 部署」）。
> 取代範圍：CR-2026-007 的 MVP 部署載體；GKE IaC 不刪，降級為 **scale 目標**。

## 脈絡
CR-2026-007 規格化了 GKE Autopilot + Cloud SQL + Memorystore 堆疊並通過本機 gate；對真實專案 `terraform plan` = 41 資源（MVP 省錢版 ~US$100–130/月）。但：
- 商業 **Gate A（≥5 房仲預付）未驗證**；MVP 單租戶、`mem0` 關、第一週 killer 是文案/說帖（零客戶 PII）。
- GKE 的價值（自動擴縮、自癒、多租戶密度、宣告式 NetworkPolicy）此階段用不到 → 過早投資。

## 決策
MVP 改用 **單台 GCE VM + docker-compose**（[`../../deploy/vm/`](../../deploy/vm/)）：
- 月費 ~US$30–55（省 Cloud SQL/Memorystore/NAT 固定費）。
- **一店一 VM** = 最強部署隔離，最貼 02-spec「部署隔離：一店一 home」。
- 同一套 container image → Gate A 後切 GKE（CR-2026-007）平滑遷移。

## 取捨（誠實揭露）
| 面向 | VM(MVP) | GKE(scale) |
|---|---|---|
| 成本 | ✅ 低 | 高（固定費） |
| 隔離(Inv-1) | ✅ 整機 | namespace |
| 不可繞過 egress(DI-4) | ⚠️ docker internal net + iptables（稽核較弱） | ✅ NetworkPolicy 宣告式 + conftest gate |
| 資料 durability(Inv-3) | ⚠️ 自管 Postgres + pg_dump | ✅ Cloud SQL HA/PITR |
| 擴縮/自癒 | ❌ 無 | ✅ |

## 緩解（VM 階段必做）
- DI-4：app 容器 `internal:true` 網路 + `HTTPS_PROXY=envoy` + **GCP VM firewall egress 規則**；以 iptables 規則測試取代 K8s conftest。
- Inv-3/PII：audit/租戶表套 `REVOKE UPDATE,DELETE`；`pg_dump → GCS` 定時；客戶 PII 量大時該表改 Cloud SQL（hybrid）。

## 觸發遷回 GKE 的條件
Gate A 通過、多店並存需求、需 HA/自動擴縮、或合規稽核要求宣告式網路政策。

## 影響
- 新增 `deploy/vm/`（compose/Dockerfile/startup/README）。
- CR-2026-007 gates.md 標註：MVP 載體改 VM（本 ADR）；GKE = scale。
- 後續可開 CR-2026-009 收斂 VM 的 egress firewall 測試 + 備份 + 佔位 image 的 Dockerfile。
