# language: zh-TW
@data @gateway @pii @gateB
功能: PII 於 Gateway egress 強制遮罩（DI-1）
  作為 平台
  我要 在資料寫入 mem0 / 回 agent 前於 Gateway 遮罩 PII
  以便 因應實登 2.0 來源未脫敏（R1），個資不外洩

  背景:
    假設 實價登錄來源門牌/地號完整揭露、未脫敏（R1）
    而且 PII 插件 hook 在「MCP post-tool 回傳 / 寫 mem0 前」執行

  場景: lvr 回傳的門牌/地號於 egress 遮罩
    假設 lvr-mcp 回傳含完整門牌「信義區OO路123號」與地號的列
    當 結果經過 Gateway PII 插件
    那麼 對外輸出 應 為脫敏（如「信義區OO路***」）
    而且 原始門牌/地號 不應 落入 mem0
    # 主 spec C2：命中 PII 記錄
    而且 應發出事件 "PiiAccessLogged"

  場景: 法人統編保留、自然人識別遮罩
    假設 資料含法人統編與自然人負責人姓名
    當 經過 PII 插件
    那麼 法人統編 應 保留
    而且 自然人姓名 應 被遮罩

  場景: 只在 LLM I/O 遮罩不合格（hook 時點）
    假設 PII 遮罩僅掛 LLM input/output hook、未掛 post-tool hook
    那麼 此設定 應 視為不合規（原始 PII 已落 mem0）
    # 驗收：遮罩時點必須早於 mem0 寫入

  場景: 出向流量強制經 Gateway
    當 任一 MCP server 或 agent 嘗試以非 Gateway 路徑直連外部來源
    那麼 該直連 應 被網路層封鎖
    而且 egress 遮罩 不應 被繞過
