# Change Intent — CR:2026:004 MCP server 接真實資料 ingest

> STDD×VDD Change Package。為 `mcp-lvr` / `mcp-public-safety` 加上**真實 open data ingest**（取代測試用 args）。

## Change Intent

- **lvr**：自內政部 plvr 季下載 ZIP（`DownloadSeason?season=115S1&type=zip&fileName=lvr_landcsv.zip`，14MB，UTF-8 雙表頭）→ 解析 → rows 餵 `query_market`。
- **public-safety**：自 data.gov.tw 「犯罪資料」(dataset 14200) CSV（鄉鎮市區級，無經緯度）→ 解析聚合 → stats 餵 `area_crime_stats`。

## 已查證真實格式（2026-06）

- plvr CSV 欄位(0-idx)：0=鄉鎮市區、1=交易標的、7=交易年月日(**ROC「1151024」**)、15=建物移轉總面積㎡、21=總價元、22=單價元㎡、25=車位總價元；前 2 列為中/英表頭。
- 犯罪 CSV：`type,oc_year(ROC),oc_data(MMDD),oc_county,oc_region` + 中文標籤列；**區域級無點位**（符 DI-5）。

## 邊界（STDD 硬約束）

- **parser 為純函式**（CSV text → rows），STDD×VDD 可測核心。
- **fetcher 以 DI 注入**（urllib live fetcher / 測試 fake）；download 為 I/O。
- ROC 日期 → ISO 轉換後交 `timestamp_guard`（Inv-4）；**production 用真實系統時鐘**（plvr 含 env-today 之後日期，guard 正確過濾）。
- public-safety 維持**區域級**，ingest **不得**引入點位（DI-5）。

## Definition of Ready
- [x] Intent / Delta / Impact / Verification Plan / Acceptance（parser 測試）
