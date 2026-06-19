# Change Intent — CR:2026:001 public-safety-mcp

> STDD×VDD Change Package（治理頁 03/07）。本 CR 把先前 P2 暫緩的 `public-safety-mcp` 以 Delta Spec 方式納入，不重寫整套規格。

## Change Intent

為房仲「物件周邊安全」場景，新增 `public-safety-mcp`：提供**交通事故周邊密度**、**區域治安統計**與**防詐查核**，全部來自警政署/165 官方 open data。

## 動機

- 帶看/委託時客戶常問周邊治安；目前無資料層支援。
- 既有研究（decision-matrix C 區）已確認官方 open data 可得且法遵🟢。

## 邊界（刻意限制，STDD 硬約束）

- **僅官方 open data**，不爬 `ba.npa.gov.tw`、不消費第三方 hosted MCP。
- **治安粒度封頂（DI-5）**：A1/A2 以周邊密度聚合呈現、犯罪資料止於鄉鎮市區；**禁門牌/點位級精準、禁對物件貼負面標籤、禁區域統計套單一物件**。
- 不含個資（A1/A2 不含肇事人姓名車號；犯罪資料為彙總）。
- 防詐（REQ:PUBSAFE:003）為 P3，無地理粒度，可後置。

## Definition of Ready（頁 03，須全具備才進實作）

- [x] Change Intent 明確（本檔）
- [x] Delta Spec 已建立（[`delta.yaml`](delta.yaml)）
- [x] Impact Analysis 已完成（[`impact.md`](impact.md)）
- [x] 受影響 Stable ID 已列出（delta.yaml `affected`）
- [x] Acceptance Scenario 已核准（[`../../features/public-safety.feature`](../../features/public-safety.feature)）
- [x] Verification Plan 已定義（[`verification-plan.yaml`](verification-plan.yaml)）
