"""LVR 真實資料 ingest（plvr 季 ZIP）。parser 純函式；fetcher 以 DI 注入。
追溯: spec-kit/05-data-mcp/changes/CR-2026-004-real-ingest/ +
      CR-2026-009-presale-schema-fix/（修預售檔欄位錯位 + 建物類型誤判）。

plvr 兩檔欄位**佈局不同**（逐欄核對 115S1）：
  - 成屋檔 a_lvr_land_a.csv（不動產買賣）= 33 欄
  - 預售檔 a_lvr_land_b.csv（預售屋買賣）= 31 欄
  兩檔的面積/總價/車位等欄索引不一致，故**以中文表頭動態定位**而非硬編固定索引
  （否則把成屋 33 欄索引套到 31 欄預售檔 → 面積/車位/單價語意錯位 → 污染行情）。

建物類型（預售/成屋）依**來源檔名**判別（_b=預售、_a/其餘=成屋）；交易標的(col1)
恆為「房地(土地+建物)」之類字串、**永不含「預售」**，不可由其判別。
"""
import csv
import io
import logging
import re
import zipfile
from datetime import date
from typing import Callable

from govnet.tls import build_secure_ssl_context, with_retry

_LOG = logging.getLogger(__name__)

# 中文表頭 → 欄位語意（正規化後 exact match）。容忍「平方公尺/㎡」與括號/斜線差異。
_HEADER_FIELD = {
    "鄉鎮市區": "district",
    "交易標的": "deal_target",
    "交易年月日": "trade_date",
    "建物移轉總面積": "area_sqm",   # 正規化已去單位；不與「土地/車位移轉總面積」相混
    "總價元": "total_price",        # exact，不與「車位總價元」相混
    "單價元": "unit_price_sqm",
    "車位總價元": "parking_price",
}
# 缺任一即無法可靠解析 → 回空（拒污染優於猜測，延續 Inv-5 精神）。
_REQUIRED_FIELDS = ("district", "deal_target", "trade_date", "area_sqm", "total_price")

_HEADER_STRIP = re.compile(r"[\s()（）/／]")
_HEADER_UNIT = re.compile(r"(平方公尺|㎡)")
_PRESALE_FILE = re.compile(r"lvr_land_b", re.IGNORECASE)


def _norm_header(h: str) -> str:
    """正規化表頭：去空白/全半形括號/斜線，並移除面積單位（平方公尺|㎡）。"""
    return _HEADER_UNIT.sub("", _HEADER_STRIP.sub("", (h or "").strip()))


def _build_col_index(header_row: list[str]) -> dict[str, int]:
    """中文表頭列 → {語意欄位: 欄索引}。首個命中為準。"""
    idx: dict[str, int] = {}
    for i, cell in enumerate(header_row):
        field = _HEADER_FIELD.get(_norm_header(cell))
        if field and field not in idx:
            idx[field] = i
    return idx


def building_type_for(filename: str) -> str:
    """依 plvr 來源檔名判別建物類型：*lvr_land_b*=預售屋買賣→「預售」；其餘→「成屋」。
    交易標的欄永不含「預售」字樣，故不可由其判別（CR-2026-009 Bug 1）。"""
    return "預售" if _PRESALE_FILE.search(filename or "") else "成屋"


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
    """plvr 單一縣市 CSV → rows。第 0 列為中文表頭→動態定位欄位（成屋/預售檔通用）；
    第 0/1 列為中/英表頭，資料自第 2 列起；ROC→ISO，無效日期或欄位缺失略過。"""
    reader = list(csv.reader(io.StringIO(text)))
    if not reader:
        return []
    col = _build_col_index(reader[0])
    if any(f not in col for f in _REQUIRED_FIELDS):
        return []  # 表頭無法辨識 → 不硬猜
    max_idx = max(col.values())
    rows: list[dict] = []
    for r in reader[2:]:  # 跳過中/英兩列表頭
        if len(r) <= max_idx:
            continue
        iso = roc_to_iso(r[col["trade_date"]])
        if iso is None:
            continue
        rows.append({
            "district": r[col["district"]],
            "deal_target": r[col["deal_target"]],
            "trade_date": iso,
            "area_sqm": _to_float(r[col["area_sqm"]]),
            "total_price": _to_int(r[col["total_price"]]),
            "unit_price_sqm": _to_int(r[col["unit_price_sqm"]]) if "unit_price_sqm" in col else 0,
            "parking_price": _to_int(r[col["parking_price"]]) if "parking_price" in col else 0,
        })
    return rows


def ingest_lvr(fetcher: Callable[[str], bytes], season: str, counties: list[str]) -> list[dict]:
    """fetcher(season)→ZIP bytes；解壓指定縣市檔→parse→合併。fetcher 注入(DI)。
    依來源檔名標註 building_type（預售/成屋），下游 ETL 不再靠交易標的字串誤判。"""
    rows: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(fetcher(season))) as z:
        names = set(z.namelist())
        for name in counties:
            if name not in names:
                continue
            text = z.read(name).decode("utf-8-sig")
            parsed = parse_lvr_csv(text)
            if not parsed:
                # 檔在 ZIP 內卻 0 筆 → 多半是表頭改名/單位記法變動（schema 漂移）使
                # _build_col_index 找不到必填欄，或確為空檔。不可靜默吞掉（否則
                # 既有成屋檔 ingest 會無聲歸零），出聲讓部署日誌/CI 可偵測。
                _LOG.warning(
                    "plvr 檔 %s 解析 0 筆：疑表頭漂移（欄位改名/單位記法變動）或空檔，"
                    "請核對 plvr schema 與 _HEADER_FIELD 對應。", name)
            btype = building_type_for(name)
            for row in parsed:
                row["building_type"] = btype
                rows.append(row)
    return rows


def live_fetch_plvr(season: str) -> bytes:
    """deploy-time live fetcher：下載 plvr 季 ZIP，走 build_secure_ssl_context（驗證仍開）+ 有界重試。"""
    import urllib.request
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    ctx = build_secure_ssl_context()

    def _fetch() -> bytes:
        with urllib.request.urlopen(url, timeout=60, context=ctx) as resp:  # noqa: S310 (官方來源)
            return resp.read()

    return with_retry(_fetch, retries=3, backoff_base=2.0)
