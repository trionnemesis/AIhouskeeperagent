"""真正部署入口：設定 path 並 mcp.run()。

用法：
  python scripts/serve.py lvr
  python scripts/serve.py public-safety
環境：
  DATA_MCP_DB   快取 db（預設 <repo>/var/data_mcp.db；GKE/VM 用 postgresql://...）。
  MCP_TRANSPORT 預設 http（streamable-http；spec 要求）；容器/網路部署勿用 stdio。
  MCP_HOST/MCP_PORT 預設 0.0.0.0:8080。
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in ("packages/govnet", "packages/datastore", "packages/mcp-lvr", "packages/mcp-public-safety"):
    sys.path.insert(0, str(ROOT / p))
os.environ.setdefault("DATA_MCP_DB", str(ROOT / "var" / "data_mcp.db"))


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "lvr"
    if which == "lvr":
        import lvr_mcp.server as srv
    elif which in ("public-safety", "public_safety", "ps"):
        import public_safety_mcp.server as srv
    else:
        raise SystemExit(f"unknown server '{which}' (use: lvr | public-safety)")
    transport = os.environ.get("MCP_TRANSPORT", "http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8080"))
    print(f"[serve] starting {which} mcp; transport={transport} {host}:{port}; "
          f"DATA_MCP_DB={os.environ['DATA_MCP_DB']}")
    if transport == "stdio":
        srv.mcp.run()  # 僅本地/in-memory；容器無 stdin 會 EOF 退出
    else:
        srv.mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
