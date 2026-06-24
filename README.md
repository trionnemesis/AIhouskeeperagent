# 房仲第二大腦 · Hermes Real-Estate Agent

[![CI](https://github.com/trionnemesis/AIhouskeeperagent/actions/workflows/ci.yml/badge.svg)](https://github.com/trionnemesis/AIhouskeeperagent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Node](https://img.shields.io/badge/node-22-green)
![status](https://img.shields.io/badge/stage-MVP%20spec%2Bdeploy-orange)

> 以 **Hermes-Agent（pinned）為底座 + mem0（記憶）+ Node/Python MCP（領域/資料）+ LINE bot（觸點）** 的房仲 AI 第二大腦。
> 本 repo 為 **Spec-Driven Development 規格包 + 資料 MCP 實作 + 部署落地（VM / GKE）**，皆走 **STDD×VDD** 治理（RED→GREEN→VDD→DEPLOY）。

## 立場（三項硬約束，貫穿全 repo）

1. **多租戶 / PII 隔離 = P0 上線 blocker**：所有查詢硬約束 `WHERE tenant_id=?`（Inv-1）；隔離未就緒前禁接 mem0（Inv-7）。
2. **即時行情降級為輔助**：資料延遲 3–5 月 + 日期垃圾值 → TimestampGuard + 拒答優於猜測（Inv-4/5）。
3. **真護城河 = 結構化客戶記憶 + 配對**（Core Domain），非行情。

> ⚠️ 商業 Gate A（付費意願）尚未驗證。本 repo 是「**怎麼蓋**」的技術契約，不是「該不該蓋」的承諾。

## 架構（演進版）

```
LINE / Web / Admin → FastAPI Edge → AI Gateway（Policy/PII/Router/ToolAuthZ/RAG, WASM；唯一不可繞過 egress）
        → Hermes runtime（pinned）+ 領域 MCP（C4–C9，mem0 經 C5 Mem0Acl）
        → 資料 MCP（lvr / public-safety / amenities / company-registry）→ 官方 open data
```

## Repo 結構

| 路徑 | 內容 |
|---|---|
| [`spec-kit/`](spec-kit/) | DDD 事件風暴 / spec / BDD / roadmap / 資料 MCP / **GKE 平台規格** |
| [`packages/`](packages/) | Python：`govnet`（TLS/retry）、`datastore`（SQLite+Postgres）、`mcp-lvr`（plvr 實價登錄 ingest，成屋(33欄)/預售(31欄)雙 schema **以中文表頭動態定位**欄位）、`mcp-public-safety` |
| [`shared/`](shared/) | TypeScript：`tw-utils`（台灣 deterministic 工具）、`scope-helper`（租戶 scope 注入） |
| [`deploy/`](deploy/) | **VM**（compose + Dockerfile，MVP）、**GKE**（Terraform + Kustomize + conftest，scale）、`verify.sh` |
| [`scripts/`](scripts/) | `serve.py`（MCP server 入口，streamable-http）、`etl_run.py`、`deploy_smoke.py` |
| [`.github/workflows/`](.github/workflows/) | CI：Python+Node 測試 + GATE:DEPLOY smoke + manifest gate |

## 快速開始 / 測試

```bash
# Python（核心邏輯/ETL 零依賴 stdlib；server/smoke 需 fastmcp）
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
(cd packages/govnet            && PYTHONPATH=. python -m unittest discover -s tests)
(cd packages/mcp-lvr           && PYTHONPATH=.:../govnet python -m unittest discover -s tests)
(cd packages/mcp-public-safety && PYTHONPATH=.:../govnet python -m unittest discover -s tests)
(cd packages/datastore         && PYTHONPATH=. python -m unittest discover -s tests)   # PG 測試需 DATABASE_URL
python scripts/deploy_smoke.py                                                          # GATE:DEPLOY

# Node（零依賴，Node 22 內建 TS type-stripping）
(cd shared/scope-helper && node --test)
(cd shared/tw-utils     && node --test)

# GKE manifest gate（需 docker；以容器跑 conftest/kubeconform）
bash deploy/verify.sh
```

## 部署

- **MVP：單 VM + docker-compose**（省錢、貼合「部署隔離 一店一 VM」）→ [`deploy/vm/`](deploy/vm/)、[ADR-001](spec-kit/06-platform-gke/adr-001-vm-for-mvp.md)
- **規模化：GKE Autopilot**（私有叢集 + Envoy egress + Cloud SQL/Redis）→ [`deploy/k8s/`](deploy/k8s/)、[CR-2026-007](spec-kit/06-platform-gke/changes/CR-2026-007-gke-deployment/)

## 文件

- 📋 [測試與部署驗證報告](TEST-REPORT.md)
- 📐 [Spec Kit 總覽](spec-kit/README.md) · [系統架構](spec-kit/02-spec/system-architecture.md) · [資料 MCP](spec-kit/05-data-mcp/README.md)
- 🚀 [GKE 平台規格](spec-kit/06-platform-gke/README.md)

## 慣例

繁中 + EN technical terms。標記 `🟢 現成`／`🟡 需補`／`🔴 新增`。所有估計值須以 POC/實測驗證。
