import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List
from app.models import FileInfo
from pathlib import Path

router = APIRouter()
base_path = Path.cwd() / "output"

def get_file_info(path: Path) -> FileInfo:
    """获取文件或目录的信息"""
    stat = path.stat()
    return FileInfo(
        name=path.name,
        path=str(path),
        is_dir=path.is_dir(),
        size=stat.st_size,
        modified_time=datetime.fromtimestamp(stat.st_mtime)
    )

def is_text_file(file_path: str) -> bool:
    """检查是否为文本文件"""
    text_extensions = {
        '.txt', '.log', '.json', '.yml', '.yaml', '.xml', '.md', '.csv',
        '.py', '.js', '.html', '.css', '.sh', '.bat', '.ini', '.conf',
        '.properties', '.env', '.cfg', '.toml'
    }
    return Path(file_path).suffix.lower() in text_extensions

@router.get("/list/{path:path}", response_model=List[FileInfo])
async def list_directory(path: str = ""):
    """列出指定目录下的文件和子目录"""
    try:
        # 转换为绝对路径并进行安全检查
        target_path = (base_path / path).resolve()
        
        # 确保路径不会超出基础目录
        if not str(target_path).startswith(str(base_path)):
            raise HTTPException(
                status_code=403,
                detail="Access to parent directory is not allowed"
            )
        
        if not target_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Path not found"
            )
            
        if not target_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Path is not a directory"
            )
        
        # 获取目录内容
        items = []
        for item in target_path.iterdir():
            # 跳过隐藏文件
            if item.name.startswith('.'):
                continue
            items.append(get_file_info(item))
        
        # 按照文件夹在前，文件在后，然后按名称排序
        return sorted(
            items,
            key=lambda x: (not x.is_dir, x.name.lower())
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list directory: {str(e)}"
        )

@router.get("/read/{path:path}")
async def read_file(path: str):
    """读取文件内容"""
    try:
        # 转换为绝对路径并进行安全检查
        file_path = (base_path / path).resolve()
        
        # 确保路径不会超出基础目录
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(
                status_code=403,
                detail="Access to parent directory is not allowed"
            )
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
            
        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail="Path is not a file"
            )
        
        # 检查文件大小
        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File is too large to read"
            )
        
        # 检查是否为文本文件
        if not is_text_file(str(file_path)):
            raise HTTPException(
                status_code=400,
                detail="File type not supported"
            )
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "content": content,
                "file_info": get_file_info(file_path)
            }
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File is not a valid text file"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )

@router.get("/info/{path:path}", response_model=FileInfo)
async def get_path_info(path: str):
    """获取文件或目录的详细信息"""
    try:
        target_path = (base_path / path).resolve()
        
        if not str(target_path).startswith(str(base_path)):
            raise HTTPException(
                status_code=403,
                detail="Access to parent directory is not allowed"
            )
        
        if not target_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Path not found"
            )
        
        return get_file_info(target_path)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get path info: {str(e)}"
        ) 