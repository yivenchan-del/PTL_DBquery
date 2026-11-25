import sqlite3
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
import uvicorn

DB_PATH = r"C:\Users\C\Downloads\PTL\sortAi.db"

app = FastAPI(title="WCS SQLite Read Service")


def get_ro_conn() -> sqlite3.Connection:
    # 使用只读 URI 模式，避免对原库产生任何写锁或修改
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10.0)
    conn.execute("PRAGMA busy_timeout = 10000;")
    conn.execute("PRAGMA query_only = ON;")
    conn.row_factory = sqlite3.Row
    return conn


BASE_JOIN_SQL = """
SELECT
    c.id              AS chute_id,
    c.name            AS chute_name,
    c.physicalIdx     AS physical_idx,
    c.orderNo         AS order_no,
    c.orderNum        AS order_num,
    c.led             AS led,
    p.id              AS pac_id,
    p.chuteName       AS pac_chute_name,
    p.physicalChute   AS physical_chute,
    p.status          AS pac_status,
    p.barcode         AS barcode,
    p.release         AS is_release,
    p.releaseAt       AS releaseAt,
    p.detail          AS detail
FROM wcs_sow_wall_chute c
LEFT JOIN wcs_pac_info p
    ON TRIM(CAST(c.physicalIdx AS TEXT)) = TRIM(CAST(p.physicalChute AS TEXT))
"""

PAC_DETAIL_FIRST_SQL = """
SELECT
    p.id              AS pac_id,
    p.chuteName       AS pac_chute_name,
    p.physicalChute   AS physical_chute,
    p.status          AS pac_status,
    p.barcode         AS barcode,
    p.release         AS is_release,
    p.releaseAt       AS releaseAt,
    p.detail          AS detail
FROM wcs_pac_info p
WHERE p.detail IS NOT NULL
  AND INSTR(p.detail, ?) > 0
ORDER BY p.id ASC
LIMIT 1
"""


def query_by_led(conn: sqlite3.Connection, led: str) -> List[Dict[str, Any]]:
    # 1. 查询 wcs_sow_wall_chute 中指定 led 的记录及 orderNo
    chute_rows = conn.execute(
        """
        SELECT
            c.id          AS chute_id,
            c.name        AS chute_name,
            c.physicalIdx AS physical_idx,
            c.orderNo     AS order_no,
            c.orderNum    AS order_num,
            c.led         AS led
        FROM wcs_sow_wall_chute c
        WHERE c.led = ?
        ORDER BY c.id ASC
        """,
        (led.strip(),),
    ).fetchall()

    # 缓存同一 orderNo 的 first pac 记录，避免重复扫描
    pac_cache: Dict[str, Optional[Dict[str, Any]]] = {}
    results: List[Dict[str, Any]] = []

    for c_row in chute_rows:
        item = dict(c_row)
        order_no = item.get("order_no")

        pac_data: Optional[Dict[str, Any]] = None
        if order_no:
            order_str = str(order_no).strip()
            if order_str:
                if order_str not in pac_cache:
                    # 2. 查询 wcs_pac_info 中 detail 包含 orderNo 的第一条记录
                    p_row = conn.execute(PAC_DETAIL_FIRST_SQL, (order_str,)).fetchone()
                    pac_cache[order_str] = dict(p_row) if p_row else None
                pac_data = pac_cache[order_str]

        if pac_data:
            item.update(pac_data)
        else:
            item.update({
                "pac_id": None,
                "pac_chute_name": None,
                "physical_chute": None,
                "pac_status": None,
                "barcode": None,
                "is_release": None,
                "releaseAt": None,
                "detail": None,
            })

        results.append(item)

    return results


@app.get("/api/order")
def query_by_order(
    orderNo: Optional[str] = Query(None, description="订单号"),
    physicalIdx: Optional[str] = Query(None, description="物理格口号"),
    led: Optional[str] = Query(None, description="LED 状态，例如 yellow")
):
    if not orderNo and not physicalIdx and not led:
        raise HTTPException(
            status_code=400,
            detail="请至少提供 orderNo、physicalIdx 或 led 参数"
        )

    try:
        with get_ro_conn() as conn:
            # 若传入 led，按 led 查 chute 的 orderNo，再去 pac_info 匹配 detail 包含 orderNo 的首条记录
            if led and not orderNo and not physicalIdx:
                data = query_by_led(conn, led)
                return {
                    "code": 0,
                    "count": len(data),
                    "data": data
                }

            conditions = []
            params: List[Any] = []
            if orderNo:
                conditions.append("c.orderNo = ?")
                params.append(orderNo)
            if physicalIdx:
                conditions.append("TRIM(CAST(c.physicalIdx AS TEXT)) = ?")
                params.append(physicalIdx.strip())
            if led:
                conditions.append("c.led = ?")
                params.append(led.strip())

            sql = f"{BASE_JOIN_SQL} WHERE {' AND '.join(conditions)}"
            rows = conn.execute(sql, params).fetchall()
            return {
                "code": 0,
                "count": len(rows),
                "data": [dict(row) for row in rows]
            }
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库忙或读取失败: {e}")


if __name__ == "__main__":
    # 监听 0.0.0.0:8765，供局域网内其他客户端访问
    uvicorn.run(app, host="0.0.0.0", port=8765)
