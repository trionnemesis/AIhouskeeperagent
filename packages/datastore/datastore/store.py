"""SQLite 快取 store — erd.dbml 的落地實現（REQ:DEPLOY:STORE）。

設計：
- 連線 per-call（讀多寫少；避免 sqlite3 跨執行緒限制，FastMCP 多執行緒安全）。
- ingested_at/recorded_at 以 DI 注入（時間可測，與 service 層 today 注入一致）。
- 去重：lvr 以 (district, trade_date, total_price, area_ping)；crime 以 (district, category, period)。
- provenance（DI-7）：每批 upsert 落地時記 source/authority/confidence/as_of。
- DI-5：crime_area_stats 刻意**無 lat/lng 欄**（區域級封頂，schema 即護欄）。
追溯: spec-kit/05-data-mcp/erd.dbml、changes/CR-2026-005-deploy-hardening/
"""
import math
import sqlite3
from pathlib import Path

# erd.dbml 子集（PostgreSQL → SQLite）。僅含已實際 ingest 的表 + provenance。
_SCHEMA = """
CREATE TABLE IF NOT EXISTS lvr_trades (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  district       TEXT NOT NULL,
  deal_type      TEXT NOT NULL DEFAULT 'sale',
  building_type  TEXT NOT NULL DEFAULT '',
  trade_date     TEXT NOT NULL,            -- ISO；TimestampGuard 於 service 層套用（Inv-4）
  total_price    INTEGER,
  unit_price_net REAL,                     -- 重算淨單價（非來源單價欄）
  area_ping      REAL,
  parking_price  INTEGER NOT NULL DEFAULT 0,
  project_name   TEXT,
  source         TEXT NOT NULL,            -- DI-2 顯名
  data_as_of     TEXT NOT NULL,            -- DI-3
  ingested_at    TEXT NOT NULL,
  UNIQUE (district, trade_date, total_price, area_ping)
);
CREATE INDEX IF NOT EXISTS ix_lvr_district_date ON lvr_trades (district, trade_date);

CREATE TABLE IF NOT EXISTS crime_area_stats (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  district    TEXT NOT NULL,               -- 鄉鎮市區（粒度封頂，DI-5）；刻意無 lat/lng
  category    TEXT NOT NULL,
  count       INTEGER NOT NULL,
  period      TEXT NOT NULL,
  source      TEXT NOT NULL,
  as_of       TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  UNIQUE (district, category, period)
);
CREATE INDEX IF NOT EXISTS ix_crime_district ON crime_area_stats (district, category);

CREATE TABLE IF NOT EXISTS traffic_accidents (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  lat         REAL NOT NULL,               -- 點位存庫供「周邊密度聚合」；DI-5：tool 不得回個別點
  lng         REAL NOT NULL,
  severity    TEXT NOT NULL,               -- A1|A2
  occurred_at TEXT NOT NULL,               -- ISO；Inv-4 TimestampGuard
  source      TEXT NOT NULL,
  as_of       TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  UNIQUE (lat, lng, severity, occurred_at)
);
CREATE INDEX IF NOT EXISTS ix_acc_latlng ON traffic_accidents (lat, lng);

CREATE TABLE IF NOT EXISTS provenance (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_ref  TEXT NOT NULL,
  source      TEXT NOT NULL,
  authority   TEXT NOT NULL,               -- gov|official_api|osm|...
  confidence  REAL NOT NULL,
  as_of       TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_prov_entity ON provenance (entity_type, entity_ref);
"""


def connect(db_path: str) -> sqlite3.Connection:
    """開連線。檔案路徑會自動建父目錄；':memory:' 供測試。"""
    if db_path != ":memory:":
        Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def record_provenance(
    conn: sqlite3.Connection, entity_type: str, entity_ref: str, source: str,
    authority: str, confidence: float, as_of: str, recorded_at: str,
) -> None:
    """DI-7：落地溯源。"""
    conn.execute(
        "INSERT INTO provenance (entity_type, entity_ref, source, authority, confidence, as_of, recorded_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (entity_type, entity_ref, source, authority, confidence, as_of, recorded_at),
    )


def query_provenance(conn: sqlite3.Connection, entity_type: str) -> list[dict]:
    cur = conn.execute("SELECT * FROM provenance WHERE entity_type=? ORDER BY id", (entity_type,))
    return [dict(r) for r in cur.fetchall()]


def upsert_lvr_trades(
    conn: sqlite3.Connection, rows: list[dict], source: str, data_as_of: str, ingested_at: str,
) -> int:
    """落地 lvr 行情快取（INSERT OR IGNORE 去重）。回傳實際新增筆數。"""
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO lvr_trades "
        "(district, deal_type, building_type, trade_date, total_price, unit_price_net, "
        " area_ping, parking_price, project_name, source, data_as_of, ingested_at) "
        "VALUES (:district, :deal_type, :building_type, :trade_date, :total_price, :unit_price_net, "
        " :area_ping, :parking_price, :project_name, :source, :data_as_of, :ingested_at)",
        [
            {
                "district": r["district"],
                "deal_type": r.get("deal_type", "sale"),
                "building_type": r.get("building_type", ""),
                "trade_date": r["trade_date"],
                "total_price": r.get("total_price"),
                "unit_price_net": r.get("unit_price_net"),
                "area_ping": r.get("area_ping"),
                "parking_price": r.get("parking_price", 0),
                "project_name": r.get("project_name"),
                "source": source,
                "data_as_of": data_as_of,
                "ingested_at": ingested_at,
            }
            for r in rows
        ],
    )
    added = conn.total_changes - before
    record_provenance(conn, "lvr_trade", data_as_of, source, "gov", 1.0, data_as_of, ingested_at)
    conn.commit()
    return added


def query_lvr_comps(conn: sqlite3.Connection, district: str) -> list[dict]:
    """讀指定行政區的行情 comps（供 query_market；TimestampGuard 由 service 層套用）。"""
    cur = conn.execute("SELECT * FROM lvr_trades WHERE district=? ORDER BY trade_date", (district,))
    return [dict(r) for r in cur.fetchall()]


def upsert_crime_area_stats(
    conn: sqlite3.Connection, district: str, stats: list[dict], source: str,
    as_of: str, ingested_at: str,
) -> int:
    """落地區域治安統計（鄉鎮市區級，DI-5）。回傳實際新增筆數。"""
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO crime_area_stats "
        "(district, category, count, period, source, as_of, ingested_at) "
        "VALUES (:district, :category, :count, :period, :source, :as_of, :ingested_at)",
        [
            {
                "district": district,
                "category": s["category"],
                "count": s["count"],
                "period": s.get("period", as_of),
                "source": source,
                "as_of": as_of,
                "ingested_at": ingested_at,
            }
            for s in stats
        ],
    )
    added = conn.total_changes - before
    record_provenance(conn, "crime_area_stat", district, source, "gov", 1.0, as_of, ingested_at)
    conn.commit()
    return added


def query_crime_stats(conn: sqlite3.Connection, district: str) -> list[dict]:
    """讀指定鄉鎮市區的治安統計（category/count/period）。"""
    cur = conn.execute(
        "SELECT category, count, period FROM crime_area_stats WHERE district=? ORDER BY category",
        (district,),
    )
    return [dict(r) for r in cur.fetchall()]


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """兩點球面距離（公尺）。"""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def upsert_traffic_accidents(
    conn: sqlite3.Connection, rows: list[dict], source: str, as_of: str, ingested_at: str,
) -> int:
    """落地事故點位（INSERT OR IGNORE 去重）。DI-5：點位僅供聚合，tool 不回個別點。"""
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO traffic_accidents "
        "(lat, lng, severity, occurred_at, source, as_of, ingested_at) "
        "VALUES (:lat, :lng, :severity, :occurred_at, :source, :as_of, :ingested_at)",
        [
            {"lat": r["lat"], "lng": r["lng"], "severity": r["severity"],
             "occurred_at": r["occurred_at"], "source": source, "as_of": as_of,
             "ingested_at": ingested_at}
            for r in rows
        ],
    )
    added = conn.total_changes - before
    record_provenance(conn, "traffic_accident", as_of, source, "gov", 1.0, as_of, ingested_at)
    conn.commit()
    return added


def query_accident_points_near(
    conn: sqlite3.Connection, lat: float, lng: float, radius_m: float,
) -> list[dict]:
    """半徑內事故點（bbox 粗篩 + haversine 精篩）。**內部用**：呼叫端須聚合後輸出（DI-5）。"""
    # bbox 須為超集（不可誤刪邊緣點）：經度每度隨緯度縮短，故 lng delta 用 cos(lat) 放寬。
    deg_lat = radius_m / 111_320.0
    deg_lng = radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    cur = conn.execute(
        "SELECT lat, lng, severity, occurred_at FROM traffic_accidents "
        "WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
        (lat - deg_lat, lat + deg_lat, lng - deg_lng, lng + deg_lng),
    )
    out: list[dict] = []
    for r in cur.fetchall():
        if _haversine_m(lat, lng, r["lat"], r["lng"]) <= radius_m:
            out.append(dict(r))
    return out
