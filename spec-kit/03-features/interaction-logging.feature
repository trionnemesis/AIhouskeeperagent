# language: zh-TW
@p2 @core
功能: 互動記錄（Interaction Logging）
  作為 經紀人
  我要 把帶看/斡旋/跟進記進客戶時間軸
  以便 形成可回溯的客戶經營脈絡（護城河資料沉澱）

  背景:
    假設 目前 scope 為 tenant="信義加盟A店", seat="seat-A1"
    而且 客戶 "林先生" 已建檔

  場景: 記錄帶看互動進客戶時間軸
    當 經紀人記錄一筆「帶看信義區某物件」互動
    那麼 應發出事件 "InteractionLogged"
    而且 該互動 應 出現在 "林先生" 的客戶時間軸
    而且 互動 應 硬約束於當前 tenant scope（Inv-1）

  場景: 互動記錄為唯讀沉澱，不觸發對外
    當 記錄一筆斡旋互動
    那麼 不應 自動對客戶發送任何訊息（Inv-2）
    而且 應發出事件 "AuditTrailRecorded"
