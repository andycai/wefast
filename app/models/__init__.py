from datetime import datetime
from pydantic import BaseModel

class Stats(BaseModel):
    id: int
    timestamp: datetime
    memory_usage: float
    cpu_usage: float
    network_in: float
    network_out: float

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
