# 測試與部署驗證報告 — 房仲第二大腦

> 日期：2026-06-20 · 範圍：CR-2026-001 ~ 008 + GKE/VM 部署 · 方法：STDD×VDD（RED→GREEN→VDD→DEPLOY）

## 摘要

| 面向 | 結果 |
|---|---|
| 單元/整合測試 | **全綠**（Python 4 套件 + Node 2 套件） |
| STDD×VDD 變異測試 | 每條不變量皆有變異被殺（Red Evidence 成立） |
| 真實資料 e2e | plvr / data.gov.tw 實抓落地、跨後端驗證 |
| GKE manifest gate | kustomize render + kubeconform 34/34 + conftest RED/GREEN/VDD |
| VM 實機部署（GCE） | full profile 全鏈跑通並驗證隔離/出口政策 |

## 1. 單元 / 整合測試

| 套件 | 測試數 | 內容 |
|---|---|---|
| `packages/govnet` | 5 | TLS 安全 context（CERT_REQUIRED+hostname；僅清 X509_STRICT）、有界重試退避 |
| `packages/mcp-lvr` | 19 | roc 民國日期、CSV 解析、ETL DI、排程(1/11/21)、新鮮度、季別 |
| `packages/mcp-public-safety` | 23 | 犯罪解析/聚合、全行政區批次、事故解析、DI-5 粒度、密度聚合 |
| `packages/datastore` | 8（+3 PG，需 `DATABASE_URL`） | erd 落地、去重冪等、provenance(DI-7)、traffic 半徑(bbox+haversine)、無座標欄(DI-5) |
| `shared/scope-helper` | 7 | Inv-1 tenant_id 強制注入 / 禁跨租戶覆寫 |
| `shared/tw-utils` | 24 | 統編 checksum、民國↔西元、郵遞區號、地址、捷運、ETL |

`scripts/deploy_smoke.py`（GATE:DEPLOY，FastMCP in-memory Client）：兩 server 啟動、cache-backed 工具、Inv-5 無快取→refused、DI-5 門牌→refused、聚合無座標。

## 2. STDD×VDD 變異測試（cp+diff+清 __pycache__）

| 變異 | 被殺的測試 |
|---|---|
| TLS `check_hostname=False` | 安全驗證測試（CR-005 M1） |
| 排程 `>` → `>=` | 發布日當天計算（M2） |
| store 去 `INSERT OR IGNORE`/`ON CONFLICT` | 去重冪等（M3 / PG IntegrityError） |
| store 去 provenance | DI-7 溯源（M4） |
| traffic 去 haversine | 半徑精篩（角點守護，M5） |
| `aggregate_crime_all` 只按 county | 全行政區分組（M6） |
| parse_accidents 不跳缺座標 | 座標清洗（M7） |
| `with_retry` 不重試 | 有界重試（M8） |

## 3. 真實資料 e2e

- **plvr 實價登錄**：安全 context 下載 115S1 台北市 **5366 筆** → 去重落地 **5266** → 信義區 365；erd 衍生欄 `area_ping`/`unit_price_net` 重算；provenance `authority=gov`；server `query_market_tool` 回 `provided n=365`。
- **犯罪資料（data.gov.tw 14200）全行政區批次**：opdadm 安全 context+UA fetcher → **340 群組 / 1107 列 / 329 個行政區**；DI-5 無座標欄；server 查七堵區→provided。
- **datastore Postgres 後端（CR-008）**：docker `postgres:16` 真實驗證 3 測試（去重/DI-5/半徑）；SQLite 零回歸。

## 4. GKE 部署驗證（本機，無需真實叢集）

| Gate | 工具 | 結果 |
|---|---|---|
| Terraform 靜態 | `terraform validate`（google v5） | ✅ Success + `fmt` clean；`plan` 對真實專案 = 41 資源 |
| k8s render | `kustomize build`（base + 3 overlays） | ✅ 34 資源 |
| schema | kubeconform | ✅ 34/34 valid |
| policy RED | conftest（壞 manifest） | ✅ 7 deny 全抓 |
| policy GREEN | conftest（真實 base/overlay） | ✅ 0 fail |
| policy VDD | 變異 image→latest / 移 default-deny | ✅ 各被抓、還原復綠 |

可重跑：`bash deploy/verify.sh`。

## 5. VM 實機部署（GCE `hermes-mvp`, e2-medium, asia-east1）

full profile 9 服務全 Up，實機驗證：

| 環節 | 結果 |
|---|---|
| 入向 caddy(:80) → fastapi-edge `/healthz` | `{"status":"ok"}` |
| webhook 無簽章 | 401（HMAC，SEC-4） |
| envoy 出口放行 gov | data.gov.tw=200 |
| envoy 封 591/leju（DI-4） | CONNECT 被拒（http_code 000） |
| appnet 容器直連外網 | BLOCKED（internal-only 網路） |
| 資料層 | lvr/public-safety streamable-http（Uvicorn :8080, `/mcp/` 307）+ Postgres 後端 |

> 收尾：VM 已 `stop`（TERMINATED，ephemeral IP 自動釋放，無保留靜態 IP）；殘留僅 30GB boot disk（~US$1.2/月）。

## 6. 過程中發現並修正的真實問題

1. **plvr 憑證缺 Subject Key Identifier** → OpenSSL 3.x `VERIFY_X509_STRICT` 預設拒（certifi 無效）。修：僅清 X509_STRICT，保留 CERT_REQUIRED+hostname。
2. **opdadm.moi.gov.tw 同缺 SKI** → 證明為跨來源共用 → 抽 `packages/govnet`；fetcher 加瀏覽器 UA（WAF 擋預設 UA）。
3. **`serve.py` 預設 stdio** → detached 容器 EOF 退出 → 改 streamable-http（GKE 同受惠）。
4. **envoy 黑名單漏放** → CONNECT 的 `:authority` 帶 `:443` 未命中 → deny domains 補 `:443/:80` 埠變體。

## 7. 建議（往 production）

**P0（接真實客戶資料前）**
- 商業 **Gate A（≥5 房仲預付）** 未驗證——先驗證再投產（北極星：錯價回報數）。
- **Hermes 真實 image**（pinned tag 上游 build）取代 stub；接上 fastapi-edge → Hermes 轉發。
- **Secret 注入**：Secret Manager + Workload Identity（VM 用 startup 拉 `.env`；GKE 用 External Secrets），勿入版控。
- **DI-4 稽核強化**：VM 端補 GCP firewall egress 規則（雙保險）+ iptables 規則測試；envoy proxy-wasm 5 filter 落地。
- **資料 durability**：客戶/audit 表上 Cloud SQL（或 VM Postgres + `pg_dump→GCS`）；`REVOKE UPDATE,DELETE`（Inv-3）。

**P1**
- LINE webhook 真實網域 + Caddy 自動 TLS；Cloud Armor（GKE）/ VM firewall（80/443）。
- ETL 排程上線（plvr 每旬 1/11/21；犯罪/事故）；新鮮度監控告警（DI-9）。
- 觀測性：每租戶 token/Push 用量、拒答率、北極星 dashboard。

**規模化（Gate A 後）**
- 由 VM 切 GKE（CR-2026-007 IaC 已備）；image 不變平滑遷移；多租戶 namespace-per-tenant。

## 8. 環境與限制

- 機器日期固定 2026-06-20；plvr 真實資料含未來日期 → TimestampGuard production 須用真實系統時鐘。
- 本機為 Apple Silicon(arm64)；GCE 為 amd64 → VM 上原生 build 避開跨架構問題。
- 本機無 terraform/kubeconform/conftest/psql → 以官方 docker 映像 + 真實 Postgres 容器驗證。
