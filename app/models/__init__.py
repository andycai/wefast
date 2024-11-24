from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Log(BaseModel):
    id: int
    app_id: str
    package: str
    role_name: str
    device: str
    log_message: str
    log_time: int
    log_type: str
    log_stack: Optional[str] = None
    create_at: int

class StatsRecord(BaseModel):
    id: int
    login_id: int
    app_id: int
    package: str
    product_name: str
    role_name: str
    device: str
    cpu: str
    gpu: str
    memory: int
    gpu_memory: int
    created_at: int

class StatsInfo(BaseModel):
    id: int
    login_id: int
    fps: int
    total_mem: int
    used_mem: int
    mono_used_mem: int
    mono_heap_mem: int
    texture: int
    mesh: int
    animation: int
    audio: int
    font: int
    text_asset: int
    shader: int
    pic: str
    process: str
    created_at: int

class ErrorLog(BaseModel):
    id: int
    timestamp: datetime
    level: str
    message: str
    stack_trace: str | None = None

class FileInfo(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified_time: datetime

class ShellCommand(BaseModel):
    command: str
    working_dir: str | None = None

class ShellResponse(BaseModel):
    success: bool
    output: str
    error: str | None = None
    exit_code: int
