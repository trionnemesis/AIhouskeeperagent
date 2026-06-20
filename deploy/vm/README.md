# deploy/vm/ — MVP 單 VM 部署（省錢版；spec 的「部署隔離：一店一 VM」）

> 方向修正：MVP 改用 **單台 GCE VM + docker-compose**（取代 GKE 託管堆疊）。理由/取捨見
> [`../../spec-kit/06-platform-gke/adr-001-vm-for-mvp.md`](../../spec-kit/06-platform-gke/adr-001-vm-for-mvp.md)。
> GKE IaC（CR-2026-007）保留為**規模化（Gate A 後）目標**，image 不變、可平滑遷移。

## 為何 VM（MVP）
- 月費 ~US$30–55 vs GKE 託管 ~$100–130（省下 Cloud SQL/Memorystore/NAT 固定費）。
- 一店一 VM = 最強的部署隔離（進程/FS/網路整台分開），最貼 02-spec MVP。
- 商業 Gate A 未驗證前，GKE 的自動擴縮/多租戶密度用不到。

## 組成
| 檔 | 用途 |
|---|---|
| `docker-compose.yml` | 全服務 + **出口隔離網路**（appnet internal-only / edgenet 對外）|
| `Dockerfile.data-mcp` | 本 repo 真實資料層（govnet+datastore+lvr/public-safety）|
| `startup-script.sh` | GCE 開機 bootstrap（裝 docker + compose up）|
| `.env.example` | 環境變數樣板（值經密管，勿入版控）|
| `Caddyfile` | LINE webhook 入向 TLS reverse proxy（`--profile full`）|

## 不可違背約束如何落地（對照 GKE）
| 約束 | VM 落地 | 稽核性 vs GKE |
|---|---|---|
| **DI-4 不可繞過 egress** | app 全在 `appnet`(internal:true 無對外)；唯 envoy 跨 edgenet；app 對外設 `HTTPS_PROXY=envoy`。再加 **VM 防火牆 egress 規則**雙保險 | 較弱（靠 docker network + iptables，非宣告式 NetworkPolicy）→ 需 iptables 規則測試取代 conftest |
| **Inv-1 租戶隔離** | 一店一 VM（整機隔離）| 等同或更強 |
| **Inv-3 audit append-only** | Postgres 容器套 `REVOKE UPDATE,DELETE`；`pg_dump → GCS` 定時備份 | 較弱（自管，無 PITR）→ 備份紀律或該表改 Cloud SQL |
| **SEC-4 webhook 驗章** | caddy(TLS) → fastapi-edge(HMAC) | 等同 |
| **mem0 gating** | `MEM0_ENABLED=false`；hermes 在 `--profile full` | 等同 |

## 部署步驟
1. **建 VM**（建議 `e2-medium` 4GB ~$24/月 或 `e2-standard-2` 8GB ~$49/月；Debian 12；靜態 IP；VM service account 給 `secretmanager.secretAccessor` + `storage`（備份）)。
   - 可由 `gcloud compute instances create`（IaC，推薦）或 Console（本次依指示用 Console 查看/建立）。
2. **secret**：Secret Manager 建 `hermes-mvp-env`，開機腳本拉成 `/opt/hermes/deploy/vm/.env`。
3. **啟動**：`docker compose --env-file .env up -d --build`（MVP 第一階段只起資料層；`--profile full` 起 hermes/edge/envoy/caddy 全套）。
4. **驗證**：容器內跑 `scripts/deploy_smoke.py`；確認 app 容器無法直連外網、僅經 envoy。

## 待補（與 GKE 版同性質佔位）
- hermes / domain-mcp / fastapi-edge / envoy-egress 的 image（Dockerfile/上游 build）；envoy proxy-wasm 5 filter 設定。
- VM 防火牆 egress 規則（GCP firewall：deny app egress、allow envoy）。
- `pg_dump → GCS` 備份 cron + Cloud SQL（若客戶 PII 要 durability）。
- Caddyfile（webhook 網域）。
