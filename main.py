import os
import sys
import uvicorn
from app.factory import create_app

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    # 设置工作目录
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    
    # 创建必要的目录
    os.makedirs("db", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("public/uploads", exist_ok=True)
    
    # 启动服务器
    uvicorn.run(
        app,  # 直接使用 app 实例，而不是字符串引用
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )