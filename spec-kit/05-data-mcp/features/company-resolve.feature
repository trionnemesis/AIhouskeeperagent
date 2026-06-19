# language: zh-TW
@data @company @p2
功能: 公司統編正規化（company-registry-mcp · GCIS）
  作為 平台
  我要 把建商/起造人名稱正規化為統編法人
  以便 可靠識別法人（建案↔起造人本身 blocked-on Q1）

  背景:
    假設 資料源為經濟部 GCIS 公司登記關鍵字查詢 API
    而且 GCIS 介接已遞「使用告知書」並完成 IP 白名單

  場景: 以統編去重同名/全半形/解散
    當 以名稱關鍵字查詢出現同名、繁簡、已解散等多筆
    那麼 應 以統編為 canonical key 去重
    而且 回傳 應 標示各筆 status（核准設立/解散…）

  場景: 自然人姓名遮罩、法人統編保留（DI-1）
    當 回傳含自然人負責人姓名
    那麼 自然人姓名 應 於 egress 遮罩
    而且 法人統編 應 保留

  場景: 配額超限（DI-8）
    當 對 GCIS 呼叫超出每日次數/連線上限
    那麼 應回傳錯誤碼 "SOURCE_QUOTA_EXCEEDED"

  場景: 授權目的內使用（個資法§20，Q6）
    假設 GCIS 告知書授權目的尚未涵蓋「對外提供建商查詢服務」
    那麼 落地散布該資料 應 被視為需先釐清（標 open question Q6）

  # 建案↔起造人/建照：blocked-on Q1（預售建案備查是否開放 open data），本輪無場景
