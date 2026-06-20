"""MVP 部署佔位 stub（hermes / domain-mcp 尚無真實 image）。
STUB_NAME/PORT 由環境注入；回 200 + banner，讓 VM 全套拓樸可起、驗證網路隔離與健康檢查。
**非產品**——hermes 待上游 pinned build，domain-mcp 待 C4-C9 領域實作。"""
import http.server
import os

_NAME = os.environ.get("STUB_NAME", "stub")
_PORT = int(os.environ.get("PORT", "8080"))


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"{_NAME} STUB — replace with real image\n".encode())

    def log_message(self, *args):
        pass


print(f"[{_NAME}] STUB serving on :{_PORT} — replace with real image", flush=True)
http.server.HTTPServer(("0.0.0.0", _PORT), _Handler).serve_forever()
