# 資料 MCP 架構規格

> Python **FastMCP** servers（獨立進程、streamable-http）+ **AI Gateway WASM** 雙層合規 + Hermes/mem0 接入。對齊新參考架構。

## 容器圖

```
                         LINE / Web / Admin
                                │
                         Backend API / FastAPI            ← 獨立進程
                                │
        ┌───────────────────────────────────────────────────────────┐
        │  AI Gateway  ← 唯一不可繞過的最終閘（出向流量強制經此）      │
        │  [Policy]  [PII]  [Router]  [ToolAuthZ]  [RAG Adapter]  (WASM)│
        └───────────────────────────────────────────────────────────┘
                                │ MCP client（streamable_http + ToolAuthZ Bearer）
                                ▼
                         Hermes runtime（base，per 02-spec）
                          │                         │ 客戶記憶（唯一路徑）
                          │ 資料 tool call           ▼
                          │                  C5 customer-crm-mcp ─Mem0Acl─▶ mem0
                          │                  (tenant:seat:customer namespace
                          │                   + scope 二次校驗, Inv-7/Inv-1)
        ┌───────────────┬─┴─────────────┬──────────────────┐
        ▼               ▼               ▼                  ▼
   ┌──────────┐   ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐
   │ lvr-mcp  │   │ amenities-mcp│  │ public-safety │  │ company-registry-mcp│
   │ (P0)🟢   │   │ (P1)🟡       │  │ -mcp (P2,後)  │  │ (P2 部分)🟡         │
   └────┬─────┘   └──────┬───────┘  └───────────────┘  └─────────┬──────────┘
        │ 每個 = 獨立 uvicorn 進程, stateless_http=True            │
        ▼                ▼                                         ▼
   plvr ZIP        TDX API / open-data CSV / TGOS geocode     GCIS API
   (內政部)        (出向皆強制經 Gateway egress)               (白名單)

   ※ mem0 不由 Hermes 或資料 MCP 直連；客戶記憶一律經 C5 Mem0Acl（02-spec, Inv-7/Inv-1）。
   ※ 資料 MCP 為「共用參考資料」工具，不寫客戶 PII 入 mem0；結果經 Gateway PII 後供 agent，
     若衍生客戶記憶才經 C5 Mem0Acl 落地。
```

## 與 02-spec 架構的演進調和

本層採用使用者於本階段提供的**更新版參考架構**（FastAPI Backend + AI Gateway WASM + Hermes/mem0）。與 [`../02-spec/system-architecture.md`](../02-spec/system-architecture.md) 的對應/演進關係：

| 02-spec（先前） | 本層（演進版） | 關係 |
|---|---|---|
| Node.js Tenant Edge Gateway (Fastify) | **Backend API / FastAPI** | 演進取代：邊界/路由/驗章移至 FastAPI |
| GovernanceGate（scope/HITL/audit 中介） | **AI Gateway WASM**（Policy/PII/Router/ToolAuthZ/RAG） | 演進擴充：治理插件化為 WASM，職責不變、更可組合 |
| Hermes Python conversation_loop（pinned，零核心改動） | **Hermes runtime（base 不變）** | **不變**：內部仍是 base Hermes，pin 版本策略續用；本層僅以 MCP 接入，不改 Hermes 核心 |
| C5 customer-crm-mcp + Mem0Acl（Inv-7） | **不變，且為 mem0 唯一路徑** | **不變且強制**：資料 MCP 不繞過 Mem0Acl |

> **不可違背**：(1) 客戶記憶一律經 C5 Mem0Acl（Inv-7/Inv-1），資料 MCP 與 Hermes 皆不得直連 mem0；(2) Hermes 仍 pin 版本、零核心改動（02-spec OPS-1），本層不假設將 Hermes 改寫為 LangGraph——若採 LangChain/LangGraph 包裝接 MCP，僅為**整合 adapter**，不影響 Hermes 內部 runtime 與 pin 策略；(3) 治理權威仍在 Gateway（不可繞過）。

## 為什麼依「資料源」切分（非依能力）

各資料源的 **rate-limit / 授權 / 快取策略 / 故障域** 不同：
- `lvr`：靜態 ZIP、無 API key、可商用、行情短 TTL。
- `amenities`：TDX OAuth+收費+速率、TGOS 額度、OSM 自架——混合限制。
- `company-registry`：GCIS IP 白名單 + 告知書 + 每日上限。

獨立進程 → **blast radius 最小、可獨立 scale、`stateless_http=True` 避免 session 黏滯**。FastMCP `mount` composition **只做命名空間、不提供故障隔離**（同進程延遲傳染），真隔離靠獨立進程 + Gateway。

## 雙層縱深防禦（各司其職）

### 第 1 層：MCP server 內 FastMCP middleware（輔助/效能，**非權威邊界**）
- `RateLimitingMiddleware`：遵守 TDX/GCIS 等**來源站台**限制與配額。
- `caching`：降低對來源請求；**行情類短 TTL**（過長=報舊價）；TTL 逐源設定。
- `error-masking`：對 agent 回結構化 `DomainError`（見 [`../02-spec/error-model.md`](../02-spec/error-model.md)）。
- 業務查核寫在 tool 函式內：每坪淨單價重算、備註旗標、geocoding 信心分數、治安粒度檢查。

### 第 2 層：AI Gateway WASM（**不可繞過的最終閘**）
> FastMCP middleware 是私有概念，換 client / 直連會被繞過——**權威合規必在 Gateway**。

| 插件 | 職責（資料層相關） |
|---|---|
| **PII** | egress 出口層強制遮罩。**因 R1（實登來源未脫敏），PII 責任全在此層，且須在「MCP post-tool / 寫 mem0 前」hook 執行，非僅 LLM I/O hook** |
| **Policy** | 跨 tool 統一策略：治安中性化、嫌惡設施禁絕對化標籤、行情附資料截止日免責、來源顯名 |
| **ToolAuthZ** | 控管 agent 角色可呼叫哪些 tool；**591/leju 來源黑名單**（需法務簽核才放行） |
| **Router** | 來源路由 / 多源 fallback |
| **RAG Adapter** | 過濾刊登者個資、標 provenance + 來源權威度 |

> ⚠️ **網路層須強制所有出向流量走 Gateway**（block 直連 provider egress），否則 egress 閘可被繞過。

## Hermes 接入

資料 MCP 以標準 MCP client 接入 base Hermes（runtime 不變，per 02-spec）。下例為 **整合 adapter**（若以 LangChain/LangGraph 包裝），**不代表把 Hermes 改寫為 LangGraph**：

```python
# 整合 adapter 範例（langchain-mcp-adapters）；亦可用任一 MCP client
client = MultiServerMCPClient({
    "lvr":       {"transport": "streamable_http", "url": "...", "headers": {"Authorization": f"Bearer {tok}"}},
    "amenities": {"transport": "streamable_http", "url": "...", "headers": {"Authorization": f"Bearer {tok}"}},
})
data_tools = await client.get_tools()   # 注入 Hermes 工具集
```
- Bearer 由 **ToolAuthZ** 簽發；header 帶角色/租戶 scope。
- 傳輸用 **streamable-http**（SSE 已棄用；stdio 不利多進程/scale）。
- **客戶記憶不在此接**：mem0 一律經 02-spec **C5 customer-crm-mcp 的 Mem0Acl**（Inv-7/Inv-1），資料 MCP 不直連 mem0。
- Hermes 內部 runtime 與 pin 策略依 02-spec（OPS-1），本層僅加資料工具，**零核心改動**。

## 技術棧拍板

| 關注點 | 選型 | 理由 |
|---|---|---|
| MCP server | **Python FastMCP** | 與 FastAPI 後端同語言；strict type；middleware/composition |
| 傳輸 | streamable-http, `stateless_http=True` | 多進程、可 scale、無 session 黏滯 |
| 爬蟲（僅補缺口） | **Playwright (Python)** + 官方 `playwright-mcp` | deterministic、省 token；webwright 非預設（見 [`decision-matrix.md`](decision-matrix.md) §3） |
| Geocoding | TGOS（主）+ NLSC（備）+ 自建快取 | authoritative；低信心不輸出精準座標 |
| 快取/狀態 | Redis + 本地物化表 | 配額、provenance、月用量（見 [`erd.dbml`](erd.dbml)） |

## 顯名義務

政府源 tool 須在 metadata/輸出標「**資料來源：內政部不動產交易實價查詢服務網**」等，否則視為自始未取得開放資料授權（政府資料開放授權第1版 ≈ CC-BY 須顯名）。

## Twinkle Hub：不消費 hosted MCP，功能自建（見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md)）

- **不連 hosted MCP**：**不**呼叫 hub.twinkleai.tw 任何 MCP/skill（避免 Alpha/預付/SLA 外部依賴）；**權威源全自建官方**（plvr/TDX/各部會/GCIS），無 Twinkle fallback。
- **twtools 功能自建**：twtools 無公開可 vendor repo（僅 hosted 暴露）→ 以自建 **`shared/tw-utils`** 重實作 deterministic 函式（統編 checksum、中英地址互轉、郵遞區號/行政區碼、捷運路線）；底層資料為官方 open data，provenance `authority='gov'/'official_api'`（**非** `third_party_mcp`）。
- **沿用好慣例**（非因連 Twinkle）：Bearer（ToolAuthZ 簽發）、native MCP streamable-http、每日同步檢查、Router 路由。
- **範圍縮限房仲域**：只重實作房仲相關 deterministic 工具，不引入全 hub 廣度。
