# 房仲資料源 → MCP Server 決策矩陣

> 本文件是「搜集 + 確認方案」階段產物，**供拍板後再寫 MCP spec kit**。
> 來源：multi-agent 研究 + 對抗驗證（36 agents / 388 web 查詢，2026-06）。
> 證據標註：`verified`(外部來源佐證) / `inferred`(推導) / `unverified`(待查)。

---

## 0. 對抗驗證推翻的三個危險假設（務必內化）

| # | 草率假設 | 對抗驗證裁決 | 後果 |
|---|---|---|---|
| **R1** | 實價登錄來源已去識別化，PII 風險低 | **refuted**：2021/7 實價登錄 2.0 起**門牌/地號完整揭露、來源未脫敏**（verified） | PII 遮罩責任 **100% 落在自家 AI Gateway**，不可假設來源已脫敏 |
| **R2** | 「建案↔起造人/建商」可從實登成交 open data 取得 | **refuted**：起造人/建照**不在**實登成交 open data，屬另一套「預售屋建案備查」，且**尚未確認以批次 open data 開放** | 建案↔建商官方路徑**有缺口**，P2 confidence=low |
| **R3** | 爬 591/leju 取得活躍 listing 是可行選項 | **refuted**：591 有**公平會公處字第106084號實際裁罰先例**；leju 全站 Cloudflare Challenge + ToS 禁令 + 刑法 §358/§359 風險（verified） | 591/leju **一律禁止直接爬取** |

> 另修正：`ba.npa.gov.tw 非機器可讀` 為誤 → 警政署**有** CSV open data（dataset 14200）；TDX「免費」為 overstatement（2024/1 起有收費要點 + 速率限制）；`microsoft/Webwright` 確實存在（5.5k★，且已有 Hermes Agent 整合）。

---

## 1. 決策矩陣

圖例：法遵風險 🟢low / 🟡medium / 🔴high · 工時 S/M/L/XL · 優先序 P0–P3 · 信心 H/M/L

### A. 行情底座（實價登錄）

| 場景 | 建議取得方式 | 法遵 | 工時 | MCP 包裝 | 優先 | 關鍵 caveat | 信心 |
|---|---|---|---|---|---|---|---|
| 成交行情(買賣/租賃) | 官方 plvr ZIP 直連（本期 `/Download` + 歷史 `/DownloadSeason`），data.gov.tw 25119/77051 對 schema | 🟢 | M | `lvr-mcp`: `query_market()`；ingest JOIN main+build+land+park 重算每坪淨單價(扣車位)、備註旗標、標資料截止日 | **P0** | **R1**：來源未脫敏，PII 全在 Gateway。延遲 45 天~2 月，近 1-2 季因申報遲延/解約需重抓校正。授權=政府資料開放授權第1版(≈CC-BY，須顯名，得商用)，免費不限流量 | H |
| 預售屋成交+建案名稱 | 官方 plvr `lvr_landBcsv.zip` / data.gov.tw 139728（去識別逐筆，含建案名 `rps28`） | 🟢 | M | 併入 `lvr-mcp`: `query_presale()`；解約 30 日內申報→定期重抓近季 | **P1** | 可安全取「建案名+成交價」；但**起造人/建商不在此**（見 R2/D 區）。預售=進度價，不可與成屋直接比 | H |

### B. 生活機能 / 設施 / 座標

| 場景 | 建議取得方式 | 法遵 | 工時 | MCP 包裝 | 優先 | 關鍵 caveat | 信心 |
|---|---|---|---|---|---|---|---|
| 交通站點(捷運/台鐵/高鐵/輕軌/公車) | TDX 官方 API（OAuth2 client_credentials，token 1天），JSON/GeoJSON 直帶座標 | 🟢 | S | `amenities-mcp`: `nearby_transit()` + 自動換 token | **P1** | TDX「免費」overstated：基礎免費但 2024/1 起收費要點 + 速率限制(未註冊~50次/日)，高用量/商用可能付費 | H |
| 學校/醫院/超商名錄 | data.gov.tw / data.gcis CSV 批次(教育部6087、健保署39283、商業署超商) | 🟢 | M | `amenities-mcp`：排程 ETL 入庫 + `nearby_facility()` | **P1** | 三類名錄皆 **address-only 無經緯度**→必須自建 geocoding；data.gov.tw **非 CKAN**(`/api/3/action` 404)，須自訂 REST + 各機關 API | H |
| 地址↔座標 geocoding | TGOS 全國門牌定位(批次，authoritative)為主，NLSC 備援，自建快取 | 🟡 | M | `amenities-mcp` 內部 geocode + 信心分數；低信心不輸出精準座標 | **P1** | TGOS Lite 免申請；全國門牌定位限政府/法人/學術/產業。**每日額度官方未查得(unverified)**。誤定位=報錯位置→須信心分數+人工覆核 | M |
| 嫌惡設施(殯葬/變電所/基地台/加油站/宮廟) | 跨機關 open data 拼湊 + 自架 OSM Overpass 補座標 | 🟡 | L | `amenities-mcp`: `nearby_disamenity()`；強制中性用語+來源+時點，禁絕對化標籤 | **P2** | 無單一全國 open data，涵蓋率參差；法律敏感(影響房價/名譽)。OSM=ODbL 須署名 + share-alike | M |
| 學區劃分 | 逐縣市整合(教育部 edugissys + 各縣市 PDF/查詢系統) | 🟢 | XL | 暫不納入或標 low-confidence | **P3** | **無全國統一 open data**，多為 PDF/查詢系統、少 polygon。PDF 解析對零容忍有正確性風險，維護成本最高 | M |

### C. 治安 / 防詐

| 場景 | 建議取得方式 | 法遵 | 工時 | MCP 包裝 | 優先 | 關鍵 caveat | 信心 |
|---|---|---|---|---|---|---|---|
| 交通事故熱區 | data.gov.tw 警政署 A1/A2 CSV（**含經緯度點位、不含個資**） | 🟢 | S | `public-safety-mcp`: `traffic_accident_density()`；標時間範圍 | **P2** | 治安類**唯一可到點位**的資料(不含肇事人姓名車號)。授權第1版，ingest 仍須逐 dataset 讀 license | H |
| 刑案/治安區域評估 | data.gov.tw dataset 14200「犯罪資料」CSV(鄉鎮市區粒度) + 各縣市 + 婦幼安全警示 | 🟢 | M | `public-safety-mcp`: `area_crime_stats()`；強制標粒度/時間、**禁門牌點位化、禁「高犯罪/治安差」標籤** | **P2** | 刑案刻意降粒度到鄉鎮/分局；**絕不可把區域統計套到單一物件**(=造假，違零容忍)。汙名化/房價爭議風險高。勿爬 `ba.npa.gov.tw` 互動查詢 | M |
| 防詐查核(交易對手/網站) | 165 涉詐網站 CSV(data.gov.tw) | 🟢 | S | `public-safety-mcp`: `fraud_check()` | **P3** | 無地理粒度，對房仲關聯較低，屬加值防詐，可後置 | H |

### D. 建商 / 建案 / 法人（有缺口）

| 場景 | 建議取得方式 | 法遵 | 工時 | MCP 包裝 | 優先 | 關鍵 caveat | 信心 |
|---|---|---|---|---|---|---|---|
| 起造人/建商名稱→統編法人正規化 | 經濟部 GCIS API(公司登記關鍵字查詢) + twcompany 離線字典容錯 | 🟡 | M | `company-registry-mcp`: `resolve_company()` | **P2** | GCIS 須寄「使用告知書」做 IP 白名單 + 每日次數/連線上限；落地散布須在告知書授權目的內(**個資法§20 特定目的外利用**風險)。同名/解散/全半形須以統編去重 | M |
| 建案↔起造人/建照核發號碼 | **需先補資料源**：預售屋「建案備查」(內政部不動產資訊平台)，確認 dataset 136948 是否已開放批次 | 🟡 | L | `company-registry-mcp`(待資料源)；以建照號 `case_no` 串接，自然人起造人遮罩 | **P2** | **R2**：起造人不在實登 open data；136948 開放狀態未確認。起造人≠建商≠所有權人(常掛名地主/SPV)，須交叉統編判讀 | **L** |
| 承造人/營造廠(建照存根) | 全國**無**結構化 open data：各縣市建管逐案/建照影像 OCR + 工程會營造業登記 | 🔴 | XL | 暫不納入(缺口)；必要時隔離為獨立爬蟲子 server | **P3** | 全國無 open data；含設計/監造/負責人**自然人姓名(個資)**、TLS 憑證鏈問題、驗證碼。爬蟲=最高成本最後手段 + ToS/個資/著作風險 | L |

### E. 爬取目標（禁止直接爬）

| 場景 | 裁決 | 法遵 | 替代方案 | 關鍵 caveat |
|---|---|---|---|---|
| **591** 活躍待售/待租 listing | **禁止直接爬取** | 🔴 | 行情用官方實登；獨家活躍 listing 走 **B2B 官方授權/合作** | **公平會公處字第106084號實際裁罰**(豬豬快租爬591，罰5萬+令停止)；ToS§20 禁重製/還原工程、中高反爬 + 刑法§358/§359；listing 為自填非成交價(報錯價風險)；591 本身是 Hermes 競品 |
| **leju 樂居** 社區評價/加值 | **禁止直接爬取** | 🔴 | 核心行情走 `lvr-mcp`；獨有社區評價走商業授權 | 全站 Cloudflare Managed Challenge 403(verified)，繞過涉刑法§358/§359(LawsNote 七法案賠償破億先例)；ToS 明文禁重製/逆向；**核心資料只是政府實登衍生，爬取無新增價值** |

---

## 2. MCP Server 方案（依資料源切分，獨立進程）

| Server | 覆蓋場景 | 語言/傳輸 | 理由 |
|---|---|---|---|
| **`lvr-mcp`** 實價登錄 | 成交行情、預售屋+建案名 | Python FastMCP / streamable-http(獨立 uvicorn) | **P0 行情底座/查價主流程**。官方 ZIP 純靜態無反爬無 API key，法遵乾淨。短 cache TTL(過長=報舊價)。single source of truth |
| **`amenities-mcp`** 設施/交通/座標 | TDX 交通、學校/醫院/超商、TGOS geocoding、嫌惡設施、學區(可選) | Python FastMCP / streamable-http | P1。各源 rate-limit/快取/授權不同(TDX 收費、TGOS 額度、OSM 自架)→按源隔離。geocoding 帶信心分數 |
| **`public-safety-mcp`** 治安/防詐 | A1/A2 點位、刑案區域、婦幼警示、165 防詐 | Python FastMCP / streamable-http | P2。汙名化/個資敏感→tool 層強制中性化、粒度標註、禁門牌級精準化。**已規格化**（[`public-safety-mcp.md`](public-safety-mcp.md)，STDD×VDD CR-2026-001） |
| **`company-registry-mcp`** 建商/法人 | GCIS 統編正規化、建案↔起造人(待資料源)、承造人(缺口) | Python FastMCP / streamable-http | P2。GCIS 需白名單+告知書+流量上限→隔離管控配額。僅落地統編可佐證之法人，自然人姓名遮罩 |

> **切分原則**：依**資料源**(非能力)切，因各源的 rate-limit / 授權 / 快取策略 / 故障域不同。獨立進程 = blast radius 最小、可獨立 scale、`stateless_http=True` 避免 session 黏滯。FastMCP `mount` composition **只做命名空間、不提供故障隔離**。

---

## 3. 爬蟲策略裁決

**分層：官方優先 → 瀏覽器自動化次之 → stealth 最後手段**。本案絕大多數需求落在第一層(政府 open data/官方 API)，爬蟲應極小化。

- **技術選型**：日常/結構化擷取用 **Playwright (Python, async)**；給 agent 用選官方 **`microsoft/playwright-mcp`**(a11y-tree 驅動、deterministic、省 token)。
- **`webwright` vs `playwright`**：webwright(microsoft/Webwright, 5.5k★，已有 Hermes Agent 整合)其「LLM 自由產 script + 跑 bash」**非確定性**，僅在「多步驟長程網頁任務需可重跑 script 產物」時評估，**非預設**；須在 ToolAuthZ/Policy + container sandbox 嚴控 + judge + 人工抽查。
- **stealth**：僅用於「ToS 允許但有 Cloudflare/DataDome」站點，且只解指紋層。
- **法遵紅線(不可逾越)**：591/leju 一律禁爬，在 **ToolAuthZ 設黑名單**，須法務簽核 + 授權證明才放行。**robots.txt/業界慣例不構成法律保護傘**；ToS 與公平法見解才有拘束力。
- **維運姿態**：爬蟲類隔離成獨立子 server，失效/被封不拖垮查價主流程；擷取資料標 provenance + 來源權威度 + 信心分數 + 時效，經 PII/Policy 過濾後才入 mem0。

---

## 4. 架構整合（對齊新參考架構）

```
LINE / Web / Admin
        ↓
Backend API / FastAPI               ← 獨立進程
        ↓
AI Gateway  ← 唯一不可繞過的最終閘
   [Policy] [PII] [Router] [ToolAuthZ] [RAG Adapter]   (WASM)
        ↓
Hermes(LangGraph)/mem0  ──(langchain-mcp-adapters MultiServerMCPClient, streamable-http + Bearer)──┐
                                                                                                    ↓
                          lvr-mcp · amenities-mcp · public-safety-mcp · company-registry-mcp  (各獨立 uvicorn)
                                                                                                    ↓
                                                              政府 open data / 官方 API（出向強制走 Gateway）
```

**雙層縱深防禦（各司其職）**：

1. **MCP server 內 FastMCP middleware（輔助/效能，非權威邊界）**：RateLimiting(遵守 TDX/GCIS 站台限制)、caching(行情短 TTL)、error-masking；業務查核(每坪重算、備註旗標、geocoding 信心、治安粒度)寫在 tool 函式內。
2. **AI Gateway WASM（不可繞過的最終閘）**：
   - **PII**：egress 出口層強制遮罩。**因 R1（實登來源未脫敏），PII 責任全在此層，且須在「MCP post-tool / 寫入 mem0 前」hook 執行，非僅 LLM I/O hook**。
   - **Policy**：跨 tool 統一策略(治安中性化、嫌惡設施禁絕對化、行情附資料截止日免責)。
   - **ToolAuthZ**：控管角色可呼叫哪些 tool；對 591/leju 來源設黑名單。
   - **Router**：來源路由。
   - **RAG**：過濾刊登者個資、標 provenance。
   - ⚠️ **網路層須強制所有出向流量走 Gateway**(block 直連 provider egress)，否則 egress 閘可被繞過。

**顯名義務**：政府源 tool 須在 metadata/輸出標「資料來源：內政部不動產交易實價查詢服務網」等，否則視為未取得開放資料授權。

---

## 5. Open Questions（需你/法務確認，影響 spec 範圍）

| # | 問題 | 影響 | 誰能解 |
|---|---|---|---|
| Q1 | 預售屋「建案備查」(含起造人/建照號)是否已開放批次 open data？(dataset 136948) | 建案↔建商官方路徑是否成立(P2 根因) | 洽內政部地政司/不動產資訊平台 |
| Q2 | TGOS 全國門牌定位每日批次額度具體數字？ | amenities-mcp 是否需 NLSC 備援/自建 geocoder | 實測/問 TGOS |
| Q3 | TDX 2024/1 收費下，預估查詢量落免費或付費層？ | amenities-mcp 成本 | 估算呼叫量 |
| Q4 | 政府資料開放授權第1版 vs CC BY 4.0「相容≠等同」的顯名/再授權精確措辭 | 對外標示法律用語 | 法務 |
| Q5 | 繞過 Cloudflare 是否構成刑法§358/§359 對 leju/591 個案 | ToolAuthZ 放行條件 | 法務意見書 |
| Q6 | GCIS「使用告知書」授權目的是否涵蓋「落地後對外提供建商查詢服務」 | 個資法§20 風險 | 法務 + GCIS 遞件 |
| Q7 | data.gov.tw 自訂 REST API 對各 dataset 覆蓋是否完整 | ETL endpoint 逐一驗證 | 工程實作期驗 |
| Q8 | ~~Twinkle Hub 消費 vs 自建~~ **已拍板：自建，不消費 hosted MCP** | twtools 功能改自建 `tw-utils`（Q9：所用 open data 授權待確認） | **resolved**；見 [`twinkle-hub-alignment.md`](twinkle-hub-alignment.md) |

---

## 6. 建議（拍板後寫 spec kit 的範圍）

- **立即啟動**：`lvr-mcp`(P0) + `amenities-mcp`(P1)——官方資料充足、法遵 🟢、可達零容忍，是行情護城河與生活機能核心。
- **技術棧拍板**：Python FastMCP + streamable-http 獨立進程 + AI Gateway WASM 雙層合規，Hermes 經 langchain-mcp-adapters 接入。
- **三條硬約束**：(1) PII 遮罩在 Gateway egress(寫 mem0 前)強制，不假設來源已脫敏；(2) 591/leju 入 ToolAuthZ 黑名單，行情走官方實登、獨家內容走 B2B 授權；(3) 治安禁門牌級精準、禁負面標籤，行情/設施輸出附資料截止日 + 來源顯名。
- **暫緩**：建案↔起造人(P2，待 Q1)、承造人/營造廠(P3，全國無 open data，除非剛性需求不做)。
- **爬蟲**：playwright-mcp 建置但預設僅對「ToS 允許且無技術保護」站點開放，補官方缺口，不投入反爬軍備競賽。
