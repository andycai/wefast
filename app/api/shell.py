import asyncio
from fastapi import APIRouter, HTTPException
from app.models import ShellCommand, ShellResponse, ScriptParams
import os
from typing import List
from pathlib import Path

router = APIRouter()

scripts_dir = Path.cwd() / "sh"

async def run_shell_command(
    command: str,
    working_dir: str | None = None,
    env: dict | None = None
) -> ShellResponse:
    """执行shell命令，支持环境变量"""
    try:
        # 合并环境变量
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # 创建子进程
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env=process_env
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
    """执行普通命令"""
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
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
    
    scripts = []
    for file in os.listdir(scripts_dir):
        if file.endswith((".sh", ".bat", ".cmd", ".ps1")):
            scripts.append(file)
    
    return scripts

@router.post("/scripts/{script_name}", response_model=ShellResponse)
async def execute_script(
    script_name: str,
    params: ScriptParams
):
    """执行指定的脚本文件，支持参数和环境变量"""
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Script not found"
        )
    
    # 准备环境变量
    env = {
        "SCRIPT_REPOSITORY": params.repository or "",
        "SCRIPT_PLATFORM": params.platform or "",
        "SCRIPT_PUBLISH_TYPE": params.publish_type or "",
        "SCRIPT_EXT": params.ext or ""
    }

    # 准备命令行参数
    args = []
    if params.repository:
        args.append(f'"{params.repository}"')
    if params.platform:
        args.append(f'"{params.platform}"')
    if params.publish_type:
        args.append(f'"{params.publish_type}"')
    if params.ext:
        args.append(f'"{params.ext}"')

    # 根据脚本类型选择执行方式
    if script_name.endswith(".sh"):
        command = f"bash {script_path} {' '.join(args)}"
    elif script_name.endswith((".bat", ".cmd")):
        command = f"{script_path} {' '.join(args)}"
    elif script_name.endswith(".ps1"):
        command = f"powershell -File {script_path} {' '.join(args)}"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported script type"
        )
    
    # 执行脚本
    result = await run_shell_command(command, scripts_dir, env)

    # 添加执行信息到输出
    execution_info = {
        "script": script_name,
        "command": command,
        "parameters": params.dict()
    }

    if result.success:
        return ShellResponse(
            success=True,
            output=f"Execution Info:\n{str(execution_info)}\n\nOutput:\n{result.output}",
            error=result.error,
            exit_code=result.exit_code
        )
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "execution_info": execution_info,
                "error": result.error or "Script execution failed"
            }
        ) 