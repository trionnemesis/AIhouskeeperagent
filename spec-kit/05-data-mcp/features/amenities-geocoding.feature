# language: zh-TW
@data @amenities @p1
功能: 設施查詢與 geocoding（amenities-mcp）
  作為 房仲 agent
  我要 取得物件周邊交通/機能與正確座標
  以便 產生帶看說帖（無錯位置風險）

  背景:
    假設 學校/醫院/超商名錄為 address-only 無經緯度
    而且 geocoding 以 TGOS 為主、NLSC 備援、自建快取

  場景: 低信心 geocoding 不輸出精準座標（DI-6）
    當 某地址 geocode 信心分數低於閾值
    那麼 結果 outcome 應 為 "refused"，reason="low_confidence"
    而且 不應 輸出精準座標（可改回行政區級）

  場景: 周邊交通查詢附來源與 token 管理
    假設 TDX token 有效期 1 天
    當 agent 查詢周邊捷運站
    那麼 應 自動換取/快取 token（遵 TDX 速率，DI-8）
    而且 結果 應 標來源 "TDX" 與 as_of

  場景: 設施資料附 provenance 才入庫（DI-7）
    當 open-data 設施 ETL 入庫
    那麼 每筆 應 標 source/authority/confidence/as_of
    而且 未標 provenance 者 不應 入 mem0

  場景: 嫌惡設施以 OSM 補座標需署名（DI-2）
    當 以 OSM Overpass 補嫌惡設施座標
    那麼 輸出 應 標 ODbL 署名

  場景: 外部源失效降級不崩（REL-4）
    假設 TDX 或 TGOS 連線失敗
    當 agent 查詢
    那麼 系統 應 降級（回部分結果或拒答）而非崩潰
