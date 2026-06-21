# Change Intent — CR:2026:009 預售屋 schema 修正（資料正確性）

> STDD×VDD Change Package。修 `mcp-lvr` 實價登錄 ingest 兩個**資料正確性** bug；
> 本地部署松山區資料逐欄實證。錯價零容忍 → 屬正確性缺陷，非新功能。

## 背景缺陷（本地實證）

plvr 季 ZIP 內成屋檔（`a_lvr_land_a.csv`，不動產買賣）與預售檔（`a_lvr_land_b.csv`，
預售屋買賣）**欄位佈局不同**（115S1 實測：成屋 33 欄、預售 31 欄）。原 ingest 以成屋
33 欄校準的**固定欄索引**解析、且以**交易標的字串**判別建物類型，導致：

- **Bug 1 — 預售屋恆被誤標「成屋」**：`etl_run._to_erd_row` 用
  `"預售" if "預售" in deal_target else "成屋"`，但兩檔交易標的(col1)恆為
  「房地(土地+建物)」之類字串、**永不含「預售」** → 所有預售成交被標成屋。
- **Bug 2（較嚴重）— 固定欄索引錯位**：`parse_lvr_csv` 硬編 col15=面積、col21=總價、
  col22=單價、col25=車位價（成屋 schema），套到 31 欄預售檔 → 面積讀到「格局-廳」、
  總價讀到「車位總價元」、車位讀到「編號」字串 → 污染值（曾使松山區單價出現
  ~282.8 萬/坪 等異常極端值）。

## Change Intent（修法）

- **以中文表頭動態定位欄位**取代固定索引：`parse_lvr_csv` 讀第 0 列中文表頭建立
  `{語意欄位: 欄索引}`，成屋/預售檔通用，並對未來 schema 漂移有韌性；表頭無法辨識
  → 回空（拒污染優於猜測，延續 Inv-5 精神）。
- **建物類型依來源檔名判別**：新增 `building_type_for(filename)`（`*lvr_land_b*`→預售、
  其餘→成屋）；`ingest_lvr` 於每筆標註 `building_type`，`etl_run` 改讀此欄。

## 邊界（STDD 硬約束）

- `parse_lvr_csv` 維持**純函式**（CSV text → rows）；表頭解析在函式內完成、不依賴檔名。
- `building_type` 屬「來源層」事實（哪個檔）→ 由 `ingest_lvr`（知道檔名）標註，不混入純 parser。
- 不改 `guards`/`service`/`store` 介面；不新增資料源；不改 erd 欄位語意。

## Definition of Ready
- [x] Intent / Delta / Impact / Verification Plan / Traceability
- [x] RED 證據（新測試在舊碼上失敗）→ GREEN → mutation 被殺（cp+diff+清 pycache）
