from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite
from app.database import get_db
from app.models import StatsRecord, StatsInfo, StatsRecordDB, StatsRecordAPI, StatsInfoDB, StatsInfoAPI, StatsRequest
from typing import List, Optional
from datetime import datetime, time
import base64
from pathlib import Path
import aiofiles

router = APIRouter()

# 创建上传目录
UPLOAD_DIR = Path("public/uploads")
if not UPLOAD_DIR.exists():
    UPLOAD_DIR.mkdir(parents=True)

# 1. 首先是所有具体的路径
@router.get("/details")
async def get_stats_details(
    login_id: int = Query(..., description="登录ID"),
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取指定 login_id 的完整统计信息，包括基础记录和详细信息（限制1000条）"""
    try:
        # 获取基础统计记录
        async with db.execute(
            "SELECT * FROM stats_records WHERE login_id = ?",
            (login_id,)
        ) as cursor:
            record_row = await cursor.fetchone()
            if not record_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stats record not found for login_id: {login_id}"
                )
            
            # 转换为 API 模型
            # db_record = StatsRecordDB(**dict(record_row))
            # record = StatsRecordAPI.from_db(db_record)
            record = StatsRecord(**dict(record_row))

        # 获取详细统计信息（限制1000条）
        async with db.execute(
            """
            SELECT * FROM stats_infos 
            WHERE login_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1000
            """,
            (login_id,)
        ) as cursor:
            info_rows = await cursor.fetchall()
            
            # 转换为 API 模型
            infos = []
            for row in info_rows:
                # db_info = StatsInfoDB(**dict(row))
                # info = StatsInfoAPI.from_db(db_info)
                info = StatsInfo(**dict(row))
                infos.append(info)

        # 返回组合的结果
        return {
            "code": 0,
            "statsRecord": record,
            "statsInfo": infos
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats details: {str(e)}"
        )

@router.get("/info/{login_id}", response_model=List[StatsInfoAPI])
async def get_stats_info(
    login_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取指定登录ID的统计信息，限制1000条"""
    try:
        async with db.execute(
            """
            SELECT * FROM stats_infos 
            WHERE login_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1000
            """,
            (login_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
            # 转换查询结果
            stats_info = []
            for row in rows:
                db_model = StatsInfoDB(**dict(row))
                api_model = StatsInfoAPI.from_db(db_model)
                stats_info.append(api_model)
            
            return stats_info

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats info: {str(e)}"
        )

@router.delete("/before")
async def delete_stats_by_date(
    date: str = Query(..., description="删除此日期23:59:59之前的所有统计信息 (格式: YYYY-MM-DD)"),
    db: aiosqlite.Connection = Depends(get_db)
):
    """删除指定日期之前的所有统计信息"""
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

        # 删除统计记录和信息
        async with db.execute(
            "DELETE FROM stats_records WHERE created_at <= ?",
            (cutoff_time,)
        ) as cursor:
            records_deleted = cursor.rowcount

        async with db.execute(
            "DELETE FROM stats_infos WHERE created_at <= ?",
            (cutoff_time,)
        ) as cursor:
            infos_deleted = cursor.rowcount

        await db.commit()
            
        return {
            "code": 0,
            "message": f"Successfully deleted stats before {date} 23:59:59",
            "deleted_count": {
                "records": records_deleted,
                "infos": infos_deleted
            },
            "cutoff_time": cutoff_time
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete stats: {str(e)}"
        )

@router.delete("/clear/{days}")
async def clear_old_stats(days: int, db: aiosqlite.Connection = Depends(get_db)):
    """清理指定天数之前的统计信息"""
    try:
        cutoff_time = int((datetime.now().timestamp() - days * 86400) * 1000)
        
        # 删除旧记录
        async with db.execute(
            "DELETE FROM stats_records WHERE created_at < ?",
            (cutoff_time,)
        ) as cursor:
            records_deleted = cursor.rowcount

        async with db.execute(
            "DELETE FROM stats_infos WHERE created_at < ?",
            (cutoff_time,)
        ) as cursor:
            infos_deleted = cursor.rowcount

        await db.commit()
        return {
            "code": 0,
            "message": f"Stats older than {days} days cleared successfully",
            "deleted_count": {
                "records": records_deleted,
                "infos": infos_deleted
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear old stats: {str(e)}"
        )

# 2. 然后是基本的 CRUD 操作
@router.get("/", response_model=dict)
async def get_stats(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db)
):
    """获取统计记录列表，支持分页和搜索"""
    try:
        # 构建基础查询
        query = "SELECT * FROM stats_records WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM stats_records WHERE 1=1"
        params = []

        # 添加搜索条件
        if search:
            search_term = f"%{search}%"
            query += """ AND (
                role_name LIKE ? OR 
                device LIKE ? OR
                package LIKE ?
            )"""
            count_query += """ AND (
                role_name LIKE ? OR 
                device LIKE ? OR
                package LIKE ?
            )"""
            params.extend([search_term, search_term, search_term])

        # 获取总记录数
        async with db.execute(count_query, params) as cursor:
            total = (await cursor.fetchone())['total']

        # 计算分页
        offset = (page - 1) * limit

        # 添加分页和排序
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # 执行查询
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        # 转换查询结果
        stats = []
        for row in rows:
            # 使用原始字段名创建模型
            stat = StatsRecord(**dict(row))
            # row_dict = dict(row)
            # stat = StatsRecord(
            #     id=row_dict['id'],
            #     login_id=row_dict['login_id'],
            #     app_id=row_dict['app_id'],
            #     package=row_dict['package'],
            #     product_name=row_dict['product_name'],
            #     role_name=row_dict['role_name'],
            #     device=row_dict['device'],
            #     cpu=row_dict['cpu'],
            #     gpu=row_dict['gpu'],
            #     memory=row_dict['memory'],
            #     gpu_memory=row_dict['gpu_memory'],
            #     stat_time=row_dict['stat_time'],
            #     created_at=row_dict['created_at']
            # )
            stats.append(stat)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )

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

@router.post("/info", response_model=StatsInfoAPI)
async def create_stats_info(info: StatsInfoDB, db: aiosqlite.Connection = Depends(get_db)):
    """创建新的统计信息"""
    try:
        async with db.execute(
            """
            INSERT INTO stats_infos (
                login_id, fps, total_mem, used_mem, mono_used_mem,
                mono_heap_mem, texture, mesh, animation, audio,
                font, text_asset, shader, pic, process, stat_time,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (info.login_id, info.fps, info.total_mem, info.used_mem,
             info.mono_used_mem, info.mono_heap_mem, info.texture,
             info.mesh, info.animation, info.audio, info.font,
             info.text_asset, info.shader, info.pic, info.process,
             info.stat_time, int(datetime.now().timestamp() * 1000))
        ) as cursor:
            row = await cursor.fetchone()
            # 转换为 API 响应模型
            db_model = StatsInfoDB(**dict(row))
            return StatsInfoAPI.from_db(db_model)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stats info: {str(e)}"
        )

# 3. 最后是通用的 ID 路由
@router.delete("/{stats_id}")
async def delete_stats(stats_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """删除指定ID的统计记录及其相关信息"""
    try:
        # 首先获取 login_id
        async with db.execute(
            "SELECT login_id FROM stats_records WHERE id = ?",
            (stats_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stats record {stats_id} not found"
                )
            login_id = row['login_id']

        # 删除相关记录
        async with db.execute(
            "DELETE FROM stats_records WHERE id = ?",
            (stats_id,)
        ):
            records_deleted = cursor.rowcount

        async with db.execute(
            "DELETE FROM stats_infos WHERE login_id = ?",
            (login_id,)
        ):
            infos_deleted = cursor.rowcount

        await db.commit()
        return {
            "code": 0,
            "message": f"Stats {stats_id} deleted successfully",
            "deleted_count": {
                "records": records_deleted,
                "infos": infos_deleted
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete stats: {str(e)}"
        )

@router.post("/", response_model=dict)
async def create_stats(
    stats: StatsRequest,
    db: aiosqlite.Connection = Depends(get_db)
):
    """创建统计记录和详细信息"""
    try:
        # 1. 处理图片数据
        if stats.statsInfo.pic:
            try:
                # 解码 base64 数据
                image_data = base64.b64decode(stats.statsInfo.pic)
                
                # 生成图片文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                image_filename = f"screenshot_{timestamp}.jpg"
                image_path = UPLOAD_DIR / image_filename
                
                # 异步写入图片文件
                async with aiofiles.open(image_path, 'wb') as f:
                    await f.write(image_data)
                
                # 更新图片路径
                relative_path = f"uploads/{image_filename}"
                stats.statsInfo.pic = relative_path
                
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to process image: {str(e)}"
                )

        # 2. 检查并处理 stats_records 数据
        async with db.execute(
            "SELECT id FROM stats_records WHERE login_id = ?",
            (stats.statsRecord.login_id,)
        ) as cursor:
            existing_record = await cursor.fetchone()

        if existing_record:
            # 更新现有记录的 role_name
            async with db.execute(
                """
                UPDATE stats_records 
                SET role_name = ?, 
                    stat_time = ?
                WHERE login_id = ?
                RETURNING *
                """,
                (
                    stats.statsRecord.role_name,
                    stats.statsRecord.stat_time,
                    stats.statsRecord.login_id
                )
            ) as cursor:
                record_row = await cursor.fetchone()
                record = dict(record_row)
        else:
            # 插入新记录
            async with db.execute(
                """
                INSERT INTO stats_records (
                    login_id, app_id, package, product_name, role_name,
                    device, cpu, gpu, memory, gpu_memory, stat_time,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING *
                """,
                (
                    stats.statsRecord.login_id,
                    stats.statsRecord.app_id,
                    stats.statsRecord.package,
                    stats.statsRecord.product_name,
                    stats.statsRecord.role_name,
                    stats.statsRecord.device,
                    stats.statsRecord.cpu,
                    stats.statsRecord.gpu,
                    stats.statsRecord.memory,
                    stats.statsRecord.gpu_memory,
                    stats.statsRecord.stat_time,
                    int(datetime.now().timestamp() * 1000)
                )
            ) as cursor:
                record_row = await cursor.fetchone()
                record = dict(record_row)

        # 3. 插入 stats_infos 数据
        async with db.execute(
            """
            INSERT INTO stats_infos (
                login_id, fps, total_mem, used_mem, mono_used_mem,
                mono_heap_mem, texture, mesh, animation, audio,
                font, text_asset, shader, pic, process, stat_time,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (
                stats.statsInfo.login_id,
                stats.statsInfo.fps,
                stats.statsInfo.total_mem,
                stats.statsInfo.used_mem,
                stats.statsInfo.mono_used_mem,
                stats.statsInfo.mono_heap_mem,
                stats.statsInfo.texture,
                stats.statsInfo.mesh,
                stats.statsInfo.animation,
                stats.statsInfo.audio,
                stats.statsInfo.font,
                stats.statsInfo.text_asset,
                stats.statsInfo.shader,
                stats.statsInfo.pic,
                stats.statsInfo.process,
                stats.statsInfo.stat_time,
                int(datetime.now().timestamp() * 1000)
            )
        ) as cursor:
            info_row = await cursor.fetchone()
            info = dict(info_row)

        await db.commit()

        return {
            "code": 0,
            "message": "Stats created successfully",
            "data": {
                "statsRecord": record,
                "statsInfo": info
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create stats: {str(e)}"
        ) 