from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from app.database import get_db
from app.models import ErrorLog
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=List[ErrorLog])
async def get_logs(
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取错误日志列表，支持按级别和时间范围过滤"""
    try:
        query = "SELECT * FROM error_logs WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch logs: {str(e)}"
        )

@router.post("/", response_model=ErrorLog)
async def create_log(log: ErrorLog, db: aiosqlite.Connection = Depends(get_db)):
    """创建新的错误日志记录"""
    try:
        async with db.execute(
            """
            INSERT INTO error_logs (level, message, stack_trace)
            VALUES (?, ?, ?)
            RETURNING *
            """,
            (log.level, log.message, log.stack_trace)
        ) as cursor:
            await db.commit()
            row = await cursor.fetchone()
            return dict(row)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create log: {str(e)}"
        )

@router.get("/summary")
async def get_logs_summary(
    days: int = 7,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取日志统计摘要"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取各级别日志数量
        async with db.execute(
            """
            SELECT level, COUNT(*) as count
            FROM error_logs
            WHERE timestamp >= ?
            GROUP BY level
            """,
            (start_date.isoformat(),)
        ) as cursor:
            level_stats = dict(await cursor.fetchall())

        # 获取最近的错误趋势（按天统计）
        async with db.execute(
            """
            SELECT date(timestamp) as date, COUNT(*) as count
            FROM error_logs
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY date
            """,
            (start_date.isoformat(),)
        ) as cursor:
            daily_trends = dict(await cursor.fetchall())

        return {
            "total_logs": sum(level_stats.values()),
            "level_distribution": level_stats,
            "daily_trends": daily_trends
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get logs summary: {str(e)}"
        )

@router.delete("/{log_id}")
async def delete_log(log_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """删除指定的日志记录"""
    try:
        async with db.execute(
            "DELETE FROM error_logs WHERE id = ?",
            (log_id,)
        ):
            await db.commit()
            return {"message": f"Log {log_id} deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete log: {str(e)}"
        )

@router.delete("/clear/{days}")
async def clear_old_logs(days: int, db: aiosqlite.Connection = Depends(get_db)):
    """清理指定天数之前的日志"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with db.execute(
            "DELETE FROM error_logs WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        ):
            await db.commit()
            return {"message": f"Logs older than {days} days cleared successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear old logs: {str(e)}"
        ) 