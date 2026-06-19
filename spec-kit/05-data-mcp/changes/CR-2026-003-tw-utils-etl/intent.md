# Change Intent — CR:2026:003 tw-utils 完整資料 ETL

> STDD×VDD Change Package。把 `shared/tw-utils` 的最小 embedded fixture 升級為**由 ETL 從官方 open data 產出的完整資料集**。

## Change Intent

建立 tw-utils 參考資料的 **ETL 管線**：官方 open data → 純 transform → 正規化 `data/*.json` → lookup 函式讀取。最小 fixture 升級為 ETL 產出（seed 先行，完整資料由 ETL 對來源跑出）。

## 動機

- 既有 fixture 僅範例子集（postal/metro/bank/city-en）；房仲場景需完整資料。
- 依 DI-2/DI-8：逐源讀 license、顯名；ETL 每日同步。

## 邊界（STDD 硬約束）

- **transform 為純函式**（raw record → normalized），為 STDD×VDD 可測核心。
- **runner 以 DI 注入 fetcher**（測試用 fake fetcher，deterministic）；實際下載為 deploy-time I/O（需來源存取/TDX key），本 CR 不執行真實下載。
- lookup 改讀 `data/*.json`；**既有 18 測試須維持綠**（資料含 seed 值，行為不退化）。
- 不引入第三方 hosted MCP（延續 Twinkle 決策）；不新增 runtime 依賴。

## Definition of Ready

- [x] Change Intent（本檔）
- [x] Delta Spec（[`delta.yaml`](delta.yaml)）
- [x] Impact Analysis（[`impact.md`](impact.md)）
- [x] Acceptance：`test/etl-transform.test.ts` + `test/etl-run.test.ts`（+ 既有回歸）
- [x] Verification Plan（[`verification-plan.yaml`](verification-plan.yaml)）
