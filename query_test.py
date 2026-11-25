import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
import uvicorn

DB_PATH = r"D:\AppData\data.db"  # 替换为你的实际 .db 路径

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
    c.sn              AS chute_sn,
    c.physicalIdx     AS physical_idx,
    c.orderNo         AS order_no,
    c.orderNum        AS order_num,
    c.stock           AS stock,
    c.complete        AS complete,
    p.id              AS pac_id,
    p.sn              AS pac_sn,
    p.taskName        AS task_name,
    p.chuteName       AS pac_chute_name,
    p.physicalChute   AS physical_chute,
    p.status          AS pac_status,
    p.reason          AS reason,
    p.errMsg          AS err_msg,
    p.imageInfo       AS image_info,
    p.detNum          AS det_num
FROM wcs_sow_wall_chute c
LEFT JOIN wcs_pac_info p
    ON TRIM(CAST(c.physicalIdx AS TEXT)) = TRIM(CAST(p.physicalChute AS TEXT))
"""


@app.get("/api/order")
def query_by_order(
    orderNo: Optional[str] = Query(None, description="订单号"),
    physicalIdx: Optional[str] = Query(None, description="物理格口号")
):
    if not orderNo and not physicalIdx:
        raise HTTPException(status_code=400, detail="请至少提供 orderNo 或 physicalIdx 参数")

    conditions = []
    params = []
    if orderNo:
        conditions.append("c.orderNo = ?")
        params.append(orderNo)
    if physicalIdx:
        conditions.append("TRIM(CAST(c.physicalIdx AS TEXT)) = ?")
        params.append(physicalIdx.strip())

    sql = f"{BASE_JOIN_SQL} WHERE {' AND '.join(conditions)}"

    try:
        with get_ro_conn() as conn:
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
