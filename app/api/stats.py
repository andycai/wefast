from fastapi import APIRouter, Depends
import aiosqlite
from app.database import get_db
from app.models import Stats
from typing import List

router = APIRouter()

@router.get("/", response_model=List[Stats])
async def get_stats(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM stats ORDER BY timestamp DESC LIMIT 100"
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/")
async def create_stats(stats: Stats, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute(
        """
        INSERT INTO stats (memory_usage, cpu_usage, network_in, network_out)
        VALUES (?, ?, ?, ?)
        """,
        (stats.memory_usage, stats.cpu_usage, stats.network_in, stats.network_out)
    )
    await db.commit()
    return {"status": "success"} 