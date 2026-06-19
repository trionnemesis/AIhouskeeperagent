# 資料 MCP Spec Kit（Data Acquisition Layer）

> 房仲第二大腦的**資料取得層**規格。把台灣不動產公開資料包裝成自有 MCP servers，供 Hermes+mem0 agent 使用。
> 上游決策依據：[`decision-matrix.md`](decision-matrix.md)（multi-agent 研究 + 對抗驗證）。

## 範圍（已拍板 2026-06）

| 項目 | 決定 |
|---|---|
| **本輪 spec 範圍** | `lvr-mcp`(P0) + `amenities-mcp`(P1) + **AI Gateway 合規層**(PII/ToolAuthZ/Policy) |
| **爬蟲政策** | 591 / leju **入 ToolAuthZ 黑名單**；爬蟲僅用 playwright-mcp 補「ToS 允許且無技術保護」站點 |
| **建商缺口** | 暫緩：只 spec GCIS `resolve_company`（可確認）；建案↔起造人標 **blocked-on Q1**；承造人/營造廠(P3) 不做 |
| **公治安(public-safety)** | **已規格化**（P2，[`public-safety-mcp.md`](public-safety-mcp.md)）；依 STDD×VDD Change Package [`CR-2026-001`](changes/CR-2026-001-public-safety/) 產出；DI-5 治安粒度封頂 |
| **Twinkle Hub** | **不消費 hosted MCP**（無 Bearer/預付/SLA 依賴）；twtools 功能以自建 `tw-utils` 重實作（twtools 無公開 vendor repo）；data server 全自建官方源（見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md)） |

## 三條不可違背硬約束（來自對抗驗證）

1. **PII 在 Gateway egress 強制遮罩**（**R1**：實價登錄 2.0 門牌/地號完整揭露、來源未脫敏）——遮罩須在「MCP post-tool / 寫 mem0 前」hook 執行，**不可假設來源已去識別**。
2. **591/leju 禁止直接爬取**（**R3**：公平會公處字第106084號裁罰先例 + Cloudflare 規避涉刑法§358/§359）——ToolAuthZ 黑名單，需法務簽核 + 授權證明才放行。
3. **行情/設施/治安輸出附資料截止日 + 來源顯名 + 信心分數**；治安禁門牌級精準、禁負面標籤（延續主 spec kit 錯價零容忍與 Inv 系列）。

## 目錄

| 檔案 | 內容 |
|---|---|
| [`decision-matrix.md`](decision-matrix.md) | 全資料源研究 + 決策矩陣 + open questions |
| [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md) | Twinkle Hub 評估與自建決策（不消費 hosted MCP；twtools 功能自建 `tw-utils`） |
| [`architecture.md`](architecture.md) | FastMCP servers + AI Gateway WASM 雙層合規 + Hermes 接入 |
| [`invariants.md`](invariants.md) | 資料層治理不變量（DI 系列：provenance/PII-at-egress/freshness/blacklist/granularity） |
| [`lvr-mcp.md`](lvr-mcp.md) | **P0** 實價登錄 server：tools / ingest / 防護 |
| [`amenities-mcp.md`](amenities-mcp.md) | **P1** 設施/交通/geocoding server |
| [`company-registry-mcp.md`](company-registry-mcp.md) | **P2(部分)** GCIS 公司正規化；建案/承造人缺口標記 |
| [`public-safety-mcp.md`](public-safety-mcp.md) | **P2** 治安/防詐（A1/A2 密度/區域犯罪/165）；DI-5 粒度封頂；依 STDD×VDD 產出 |
| [`changes/`](changes/) | STDD×VDD Change Packages：`CR-2026-001`(public-safety)、`CR-2026-002`(Gateway Router+RAG)、`CR-2026-003`(tw-utils ETL)、`CR-2026-004`(MCP 真實資料 ingest) |
| [`gateway-compliance.md`](gateway-compliance.md) | AI Gateway **5 WASM 插件完整**：Policy/PII/Router/ToolAuthZ/RAG + 黑名單 |
| [`erd.dbml`](erd.dbml) | 資料 MCP 快取 / provenance / 配額 schema |
| [`features/`](features/) | BDD 場景（行情/PII egress/geocoding/黑名單/顯名） |

## 與主 spec kit 的關係

本層延續主 spec kit（`../00`~`../04`）的不變量與治理；資料層不變量以 **DI-** 前綴編號，避免與主 spec 的 Inv-1..10 混淆，並在相關處交叉引用。Hermes/mem0/LINE/HITL 等仍遵主 spec。

## 慣例

- 標記：🟢 官方資料充足/法遵乾淨 · 🟡 需設定/授權/補強 · 🔴 缺口/禁止。
- 證據沿用研究標註：`verified` / `inferred` / `unverified`。
