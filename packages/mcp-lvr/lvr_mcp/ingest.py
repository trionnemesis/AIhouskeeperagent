"""LVR 真實資料 ingest（plvr 季 ZIP）。parser 純函式；fetcher 以 DI 注入。
追溯: spec-kit/05-data-mcp/changes/CR-2026-004-real-ingest/
plvr CSV 欄位(0-idx): 0=鄉鎮市區 1=交易標的 7=交易年月日(ROC) 15=建物移轉總面積㎡
                      21=總價元 22=單價元㎡ 25=車位總價元；前 2 列為中/英表頭。
"""
import csv
import io
import ssl
import zipfile
from datetime import date
from typing import Callable


def roc_to_iso(roc: str) -> str | None:
    """民國日期字串(如 '1151024'/'0991231') → ISO；不合法回 None。"""
    s = (roc or "").strip()
    if not s.isdigit() or len(s) < 6:
        return None
    year = int(s[:-4]) + 1911
    mm, dd = int(s[-4:-2]), int(s[-2:])
    try:
        return date(year, mm, dd).isoformat()
    except ValueError:
        return None


def _to_int(s: str) -> int:
    s = (s or "").strip()
    return int(s) if s.lstrip("-").isdigit() else 0


def _to_float(s: str) -> float:
    try:
        return float((s or "").strip())
    except ValueError:
        return 0.0


def parse_lvr_csv(text: str) -> list[dict]:
    """plvr 單一縣市 CSV → rows（跳過 2 列表頭；ROC→ISO；無效日期略過）。"""
    reader = list(csv.reader(io.StringIO(text)))
    rows: list[dict] = []
    for r in reader[2:]:  # 跳過中/英兩列表頭
        if len(r) < 26:
            continue
        iso = roc_to_iso(r[7])
        if iso is None:
            continue
        rows.append({
            "district": r[0],
            "deal_target": r[1],
            "trade_date": iso,
            "area_sqm": _to_float(r[15]),
            "total_price": _to_int(r[21]),
            "unit_price_sqm": _to_int(r[22]),
            "parking_price": _to_int(r[25]),
        })
    return rows


def ingest_lvr(fetcher: Callable[[str], bytes], season: str, counties: list[str]) -> list[dict]:
    """fetcher(season)→ZIP bytes；解壓指定縣市檔→parse→合併。fetcher 注入(DI)。"""
    rows: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(fetcher(season))) as z:
        names = set(z.namelist())
        for name in counties:
            if name not in names:
                continue
            text = z.read(name).decode("utf-8-sig")
            rows.extend(parse_lvr_csv(text))
    return rows


def build_secure_ssl_context() -> ssl.SSLContext:
    """plvr 專用安全 TLS context。

    Why：plvr.land.moi.gov.tw 憑證鏈缺 Subject Key Identifier（RFC5280 結構不符），
    OpenSSL 3.x 預設開啟的 VERIFY_X509_STRICT 會以此拒絕。實測：certifi/補 CA 皆無效
    （非信任根缺失），唯一安全修法是**僅關閉 X509_STRICT 結構檢查**。
    信任鏈、簽章、到期、hostname 驗證全部保留（CERT_REQUIRED + check_hostname）。
    **禁止** 改 CERT_NONE 或 check_hostname=False——那會讓 MITM 可偽冒此端點。
    """
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def live_fetch_plvr(season: str) -> bytes:
    """deploy-time live fetcher：下載 plvr 季 ZIP，走 build_secure_ssl_context（驗證仍開）。"""
    import urllib.request
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    ctx = build_secure_ssl_context()
    with urllib.request.urlopen(url, timeout=60, context=ctx) as resp:  # noqa: S310 (官方來源)
        return resp.read()
