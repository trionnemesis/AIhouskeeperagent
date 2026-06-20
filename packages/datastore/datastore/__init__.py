"""資料 MCP 共用快取層（erd.dbml 的 SQLite 落地）。

單一 db = erd.dbml 的 lvr_data_mcp schema 子集（已實際 ingest 的表）。
domain-agnostic 持久化：欄位映射由各 MCP package 的 ETL runner 負責，store 只負責落地/查詢/溯源。
"""
from datastore import store  # noqa: F401
