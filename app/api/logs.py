from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite
from app.database import get_db
from app.models import Log
from typing import List, Optional
from datetime import datetime, time

router = APIRouter()

@router.get("/", response_model=dict)
async def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取错误日志列表，支持分页和搜索"""
    try:
        # 构建基础查询
        query = "SELECT * FROM logs WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM logs WHERE 1=1"
        params = []

        # 添加搜索条件
        if search:
            search_term = f"%{search}%"
            query += """ AND (
                role_name LIKE ? OR 
                log_message LIKE ?
            )"""
            count_query += """ AND (
                role_name LIKE ? OR 
                log_message LIKE ?
            )"""
            params.extend([search_term, search_term])

        # 获取总记录数
        async with db.execute(count_query, params) as cursor:
            total = (await cursor.fetchone())['total']

        # 计算分页
        offset = (page - 1) * limit
        total_pages = (total + limit - 1) // limit

        # 添加分页
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # 执行查询
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            logs = [dict(row) for row in rows]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            # "total_pages": total_pages,
            "logs": logs,
            # "has_next": page < total_pages,
            # "has_prev": page > 1
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch logs: {str(e)}"
        )

@router.post("/", response_model=Log)
async def create_log(log: Log, db: aiosqlite.Connection = Depends(get_db)):
    """创建新的日志记录"""
    try:
        async with db.execute(
            """
            INSERT INTO logs (
                app_id, package, role_name, device,
                log_message, log_time, log_type, log_stack, create_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (log.app_id, log.package, log.role_name, log.device,
             log.log_message, log.log_time, log.log_type, log.log_stack,
             int(datetime.now().timestamp() * 1000))
        ) as cursor:
            row = await cursor.fetchone()
            await db.commit()
            return dict(row)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create log: {str(e)}"
        )

@router.delete("/before")
async def delete_logs_by_date(
    date: str = Query(..., description="删除此日期23:59:59之前的所有日志 (格式: YYYY-MM-DD)"),
    db: aiosqlite.Connection = Depends(get_db)
):
    """删除指定日期之前的所有日志"""
    try:
        # 解析日期并设置为当天的23:59:59
        try:
            end_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = datetime.combine(end_date, time(23, 59, 59))
            cutoff_time = int(end_date.timestamp() * 1000)  # 转换为毫秒时间戳
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Please use YYYY-MM-DD"
            )

        # 执行删除操作
        async with db.execute(
            "DELETE FROM logs WHERE create_at <= ?",
            (cutoff_time,)
        ) as cursor:
            deleted_count = cursor.rowcount
            await db.commit()
            
            return {
                "code": 0,
                "message": f"Successfully deleted logs before {date} 23:59:59",
                "deleted_count": deleted_count,
                "cutoff_time": cutoff_time
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete logs: {str(e)}"
        )

@router.delete("/{log_id}")
async def delete_log(log_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """删除指定的日志记录"""
    try:
        async with db.execute(
            "DELETE FROM logs WHERE id = ?",
            (log_id,)
        ):
            await db.commit()
            return {
                "code": 0,
                "message": f"Log {log_id} deleted successfully"
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete log: {str(e)}"
        )

@router.delete("/clear/{days}")
async def clear_old_logs(days: int, db: aiosqlite.Connection = Depends(get_db)):
    """清理指定天数之前的日志"""
    try:
        cutoff_time = int((datetime.now().timestamp() - days * 86400) * 1000)
        
        async with db.execute(
            "DELETE FROM logs WHERE create_at < ?",
            (cutoff_time,)
        ):
            await db.commit()
            return {
                "code": 0,
                "message": f"Logs older than {days} days cleared successfully"
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear old logs: {str(e)}"
        ) 