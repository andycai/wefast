import asyncio
from fastapi import APIRouter, HTTPException
from app.models import ShellCommand, ShellResponse
import os
from typing import List

router = APIRouter()

async def run_shell_command(command: str, working_dir: str | None = None) -> ShellResponse:
    try:
        # 创建子进程
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        # 等待命令执行完成并获取输出
        stdout, stderr = await process.communicate()
        
        # 解码输出
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return ShellResponse(
            success=process.returncode == 0,
            output=output,
            error=error,
            exit_code=process.returncode
        )
    except Exception as e:
        return ShellResponse(
            success=False,
            output="",
            error=str(e),
            exit_code=-1
        )

@router.post("/execute", response_model=ShellResponse)
async def execute_command(command: ShellCommand):
    # 安全检查：禁止执行某些危险命令
    forbidden_commands = ["rm -rf", "mkfs", "dd", ":(){ :|:& };:"]
    if any(cmd in command.command.lower() for cmd in forbidden_commands):
        raise HTTPException(
            status_code=400,
            detail="Forbidden command detected"
        )
    
    # 检查工作目录是否存在
    if command.working_dir and not os.path.exists(command.working_dir):
        raise HTTPException(
            status_code=400,
            detail="Working directory does not exist"
        )
    
    # 执行命令
    result = await run_shell_command(command.command, command.working_dir)
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Command failed: {result.error}"
        )
    
    return result

@router.get("/scripts", response_model=List[str])
async def list_scripts():
    """列出可用的脚本文件"""
    scripts_dir = "scripts"  # 脚本存放目录
    
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
    
    scripts = []
    for file in os.listdir(scripts_dir):
        if file.endswith((".sh", ".bat", ".cmd", ".ps1")):
            scripts.append(file)
    
    return scripts

@router.post("/scripts/{script_name}", response_model=ShellResponse)
async def execute_script(script_name: str):
    """执行指定的脚本文件"""
    scripts_dir = "scripts"
    script_path = os.path.join(scripts_dir, script_name)
    
    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=404,
            detail="Script not found"
        )
    
    # 根据脚本类型选择执行方式
    if script_name.endswith(".sh"):
        command = f"bash {script_path}"
    elif script_name.endswith((".bat", ".cmd")):
        command = script_path
    elif script_name.endswith(".ps1"):
        command = f"powershell -File {script_path}"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported script type"
        )
    
    result = await run_shell_command(command, scripts_dir)
    return result 