"""真正部署入口：設定 path 並 mcp.run()。

用法：
  python scripts/serve.py lvr
  python scripts/serve.py public-safety
環境：DATA_MCP_DB 指向快取 db（預設 <repo>/var/data_mcp.db）。
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in ("packages/datastore", "packages/mcp-lvr", "packages/mcp-public-safety"):
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
    print(f"[serve] starting {which} mcp; DATA_MCP_DB={os.environ['DATA_MCP_DB']}")
    srv.mcp.run()


if __name__ == "__main__":
    main()
