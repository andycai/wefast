import aiosqlite
from pathlib import Path

DB_PATH = Path("db/logs.db")

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 创建日志表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT,
                package TEXT,
                role_name TEXT,
                device TEXT,
                log_message TEXT,
                log_time INTEGER,
                log_type TEXT,
                log_stack TEXT,
                create_at INTEGER
            )
        """)
        
        # 创建日志表索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_create_at ON logs(create_at)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_log_time ON logs(log_time)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_role_name_message ON logs(role_name, log_message)
        """)

        # 创建统计记录表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id INTEGER,
                app_id INTEGER,
                package TEXT,
                product_name TEXT,
                role_name TEXT,
                device TEXT,
                cpu TEXT,
                gpu TEXT,
                memory INTEGER,
                gpu_memory INTEGER,
                created_at INTEGER
            )
        """)
        
        # 创建统计记录表索引
        await db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_records_login_id 
            ON stats_records(login_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_records_created_at 
            ON stats_records(created_at)
        """)

        # 创建统计信息表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats_infos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id INTEGER,
                fps INTEGER,
                total_mem INTEGER,
                used_mem INTEGER,
                mono_used_mem INTEGER,
                mono_heap_mem INTEGER,
                texture INTEGER,
                mesh INTEGER,
                animation INTEGER,
                audio INTEGER,
                font INTEGER,
                text_asset INTEGER,
                shader INTEGER,
                pic TEXT,
                process TEXT,
                created_at INTEGER
            )
        """)
        
        # 创建统计信息表索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_infos_login_id 
            ON stats_infos(login_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_infos_created_at 
            ON stats_infos(created_at)
        """)
        
        await db.commit() 