from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys, os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的初始化操作
    yield
    # 关闭时的清理操作

def get_static_path():
    """获取静态文件目录"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'public')
    return 'public'

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=get_static_path()), name="static")
    
    # 导入和注册路由
    from app.api import stats, logs, shell, files
    
    app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
    app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
    app.include_router(shell.router, prefix="/api/shell", tags=["shell"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    
    return app
