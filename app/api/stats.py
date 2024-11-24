from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from app.database import get_db
from app.models import StatsRecord, StatsInfo
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/record", response_model=StatsRecord)
async def create_stats_record(record: StatsRecord, db: aiosqlite.Connection = Depends(get_db)):
    """创建新的统计记录"""
    try:
        async with db.execute(
            """
            INSERT INTO stats_records (
                login_id, app_id, package, product_name, role_name,
                device, cpu, gpu, memory, gpu_memory, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (record.login_id, record.app_id, record.package, record.product_name,
             record.role_name, record.device, record.cpu, record.gpu,
             record.memory, record.gpu_memory, int(datetime.now().timestamp() * 1000))
        ) as cursor:
            row = await cursor.fetchone()
            await db.commit()
            return dict(row)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stats record: {str(e)}"
        )

@router.post("/info", response_model=StatsInfo)
async def create_stats_info(info: StatsInfo, db: aiosqlite.Connection = Depends(get_db)):
    """创建新的统计信息"""
    try:
        async with db.execute(
            """
            INSERT INTO stats_infos (
                login_id, fps, total_mem, used_mem, mono_used_mem,
                mono_heap_mem, texture, mesh, animation, audio,
                font, text_asset, shader, pic, process, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (info.login_id, info.fps, info.total_mem, info.used_mem,
             info.mono_used_mem, info.mono_heap_mem, info.texture,
             info.mesh, info.animation, info.audio, info.font,
             info.text_asset, info.shader, info.pic, info.process,
             int(datetime.now().timestamp() * 1000))
        ) as cursor:
            row = await cursor.fetchone()
            await db.commit()
            return dict(row)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stats info: {str(e)}"
        )

@router.get("/records", response_model=List[StatsRecord])
async def get_stats_records(
    login_id: Optional[int] = None,
    app_id: Optional[int] = None,
    role_name: Optional[str] = None,
    limit: int = 100,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取统计记录列表"""
    try:
        query = "SELECT * FROM stats_records WHERE 1=1"
        params = []

        if login_id:
            query += " AND login_id = ?"
            params.append(login_id)

        if app_id:
            query += " AND app_id = ?"
            params.append(app_id)

        if role_name:
            query += " AND role_name = ?"
            params.append(role_name)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats records: {str(e)}"
        )

@router.get("/info/{login_id}", response_model=List[StatsInfo])
async def get_stats_info(
    login_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取指定登录ID的统计信息"""
    try:
        async with db.execute(
            "SELECT * FROM stats_infos WHERE login_id = ? ORDER BY created_at DESC",
            (login_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats info: {str(e)}"
        ) 