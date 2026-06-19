# language: zh-TW
@data @lvr @p0
功能: 實價登錄行情查詢（lvr-mcp · 防護鏈）
  作為 房仲 agent
  我要 取得可信的實登成交行情
  以便 議價輔助時不報錯價（延續錯價零容忍）

  背景:
    假設 lvr-mcp 以官方 plvr ZIP 為權威源
    而且 ingest 已 JOIN main/build/land/park 並重算每坪淨單價

  場景: 正常查詢回傳行情並附時點與顯名
    當 agent 查詢「信義區 / 成屋 / 近一年」成交行情
    那麼 結果 outcome 應 為 "provided"
    而且 每筆單價 應 為重算後淨單價（已扣車位）
    而且 應 附 data_as_of（資料更新至 YYYY-MM）與申報遲延警示（DI-3）
    而且 應 附來源顯名「內政部不動產交易實價查詢服務網」（DI-2）

  場景: 日期垃圾值被剔除（Inv-4）
    假設 來源含 trade_date="2101-10-17" 與 "1921-01-28" 的列
    當 ingest 處理資料
    那麼 該等列 應 被剔除（<2010 或 >今日+90天）

  場景: 可比交易不足即拒答（Inv-5）
    當 查詢某行政區可比交易筆數過少
    那麼 結果 outcome 應 為 "refused"，reason="insufficient_comps"
    而且 不應 輸出任何推測價

  場景: 預售屋可得建案名但無建商（R2）
    當 agent 查詢預售屋成交
    那麼 結果 應 含 project_name（建案名 rps28）
    而且 不應 宣稱可由本資料取得起造人/建商

  場景: 來源不可用時降級（REL-4）
    假設 plvr 下載失敗
    當 agent 查詢行情
    那麼 結果 outcome 應 為 "refused"，reason="source_unavailable"
    而且 系統 不應 崩潰
    # 內部對映錯誤碼 MARKET_SOURCE_UNAVAILABLE；對外為領域 refused（非 DomainError）

  場景: 行情快取過期重抓校正（DI-9）
    假設 lvr 快取超過短 TTL 或屬近 1-2 季資料
    當 agent 查詢行情
    那麼 系統 應 重抓 plvr 校正後再回
    而且 結果 應 附反映最新校正的 data_as_of
