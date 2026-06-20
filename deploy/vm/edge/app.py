"""FastAPI Edge（最小真實版）— LINE webhook HMAC-SHA256 驗章（SEC-4）。
MVP：驗章通過後 ack；轉發 Hermes 待 hermes 真實 image 就緒後接上（TODO）。
"""
import base64
import hashlib
import hmac
import os

from fastapi import FastAPI, Request, Response

app = FastAPI(title="hermes-fastapi-edge")
_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "").encode()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("x-line-signature", "")
    expected = base64.b64encode(hmac.new(_SECRET, body, hashlib.sha256).digest()).decode()
    if not _SECRET or not hmac.compare_digest(expected, sig):
        return Response(status_code=401)  # 偽造/缺簽章 → 401（SEC-4）
    # TODO: 轉發至 Hermes runtime（待真實 hermes image）；MVP 先 ack。
    return {"ok": True}
