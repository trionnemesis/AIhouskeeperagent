# language: zh-TW
@p3 @guardrail
功能: 行情錯價防護（Market Comp Guardrail · 降級為輔助）
  作為 平台
  我要 在提供行情前過完整防護鏈
  以便 寧可拒答也不報錯價（牆 1：錯價零容忍）

  背景:
    假設 行情功能定位為「輔助」，非門面、非護城河
    而且 lvr-trades 資料經 ACL 接入

  規則: TimestampGuard 過濾日期垃圾值（Inv-4）

    場景大綱: 交易日期邊界防呆
      假設 lvr 回傳一列 trade_date="<trade_date>"
      當 系統套用 TimestampGuard（下界 2010-01-01、上界 今日+90天）
      那麼 該列判定應為 "<判定>"

      例子:
        | trade_date | 判定 | 備註           |
        | 2010-01-01 | 保留 | 下界 on        |
        | 2009-12-31 | 剔除 | 低於下界       |
        | 1921-01-28 | 剔除 | lvr MIN 垃圾值 |
        | 2026-03-05 | 保留 | 報告最新有效日 |
        | 2033-03-23 | 剔除 | 未來垃圾值     |
        | 2101-10-17 | 剔除 | lvr MAX 垃圾值 |

    場景: 剔除垃圾值時發出事件
      假設 lvr 回傳含 trade_date="2101-10-17" 的列
      當 系統處理行情資料
      那麼 應發出事件 "GarbageDataFiltered"

    場景: 未加上界的「最新行情」不得直接回傳
      當 查詢「最新成交」
      那麼 系統 應 先套用 trade_date ≤ 今日+90天 上界
      而且 不應 回傳 2101 等未來日期作為「最新」

  規則: 拒答優於猜測（Inv-5）

    場景: 地址比對失敗即拒答
      假設 查詢地址無法對應到可比交易
      當 請求行情
      那麼 結果 應 為 "MarketCompRefused"，reason="addr_mismatch"
      而且 不應 輸出任何推測價

    場景: 信心不足即拒答
      假設 可比交易筆數過少導致信心分數低於閾值
      當 請求行情
      那麼 結果 應 為 "MarketCompRefused"，reason="low_confidence"

  規則: 行情標註義務（Inv-6）

    場景: 提供行情必附延遲聲明與類型標註
      假設 通過防護鏈且有足夠可比交易
      當 提供行情參考
      那麼 結果 應 為 "MarketCompProvided"
      而且 應 附「資料更新至 YYYY-MM」
      而且 應 附信心分數與預售/成屋/車位標註
      而且 話術 不應 宣稱「即時」

  規則: 外部源失效降級（REL-4）

    場景: lvr 行情源不可用即降級拒答
      假設 lvr-trades 連線超時或回 5xx
      當 經紀人查詢行情
      那麼 結果 應 為 "MarketCompRefused"，reason="source_unavailable"
      而且 系統 不應 崩潰（降級而非中斷）
      而且 應發出事件 "AuditTrailRecorded"
