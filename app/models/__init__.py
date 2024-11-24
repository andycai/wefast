from datetime import datetime
from pydantic import BaseModel, Field, computed_field
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

class StatsRecordDB(BaseModel):
    """数据库使用的统计记录模型"""
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
    stat_time: int
    created_at: int

class StatsRecordAPI(BaseModel):
    """API 使用的统计记录模型"""
    id: int
    login_id: int
    app_id: int
    package_name: str
    product_name: str
    role_name: str
    device_name: str
    system_cpu: str
    graphics_divice: str
    system_mem: int
    graphics_mem: int
    mtime: int
    created_at: int

    @classmethod
    def from_db(cls, db_model: StatsRecordDB) -> "StatsRecordAPI":
        """从数据库模型转换为 API 模型"""
        return cls(
            id=db_model.id,
            login_id=db_model.login_id,
            app_id=db_model.app_id,
            package_name=db_model.package,
            product_name=db_model.product_name,
            role_name=db_model.role_name,
            device_name=db_model.device,
            system_cpu=db_model.cpu,
            graphics_divice=db_model.gpu,
            system_mem=db_model.memory,
            graphics_mem=db_model.gpu_memory,
            mtime=db_model.stat_time,
            created_at=db_model.created_at
        )

class StatsInfoDB(BaseModel):
    """数据库使用的统计信息模型"""
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
    stat_time: int
    created_at: int

class StatsInfoAPI(BaseModel):
    """API 使用的统计信息模型"""
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
    mtime: int
    created_at: int

    @classmethod
    def from_db(cls, db_model: StatsInfoDB) -> "StatsInfoAPI":
        """从数据库模型转换为 API 模型"""
        return cls(
            id=db_model.id,
            login_id=db_model.login_id,
            fps=db_model.fps,
            total_mem=db_model.total_mem,
            used_mem=db_model.used_mem,
            mono_used_mem=db_model.mono_used_mem,
            mono_heap_mem=db_model.mono_heap_mem,
            texture=db_model.texture,
            mesh=db_model.mesh,
            animation=db_model.animation,
            audio=db_model.audio,
            font=db_model.font,
            text_asset=db_model.text_asset,
            shader=db_model.shader,
            pic=db_model.pic,
            process=db_model.process,
            mtime=db_model.stat_time,
            created_at=db_model.created_at
        )

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

class ScriptParams(BaseModel):
    """脚本执行参数"""
    repository: str | None = None
    platform: str | None = None
    publish_type: str | None = None
    ext: str | None = None

class StatsRecord(BaseModel):
    """统计记录基础模型"""

    # 方法一，字段别名
    id: int
    login_id: int
    app_id: int
    package: str = Field(..., alias="package_name")
    product_name: str
    role_name: str
    device: str = Field(..., alias="device_name")
    cpu: str = Field(..., alias="system_cpu")
    gpu: str = Field(..., alias="graphics_divice")
    memory: int = Field(..., alias="system_mem")
    gpu_memory: int = Field(..., alias="graphics_mem")
    stat_time: int = Field(..., alias="mtime")
    created_at: int

    class Config:
        # 允许通过原始字段名和别名字段名访问
        populate_by_name = True
        # 允许别名
        allow_population_by_field_name = True

    # 方法三，计算方法

    # @computed_field
    # def package_name(self) -> str:
    #     return self.package

    # @computed_field
    # def device_name(self) -> str:
    #     return self.device

    # @computed_field
    # def system_cpu(self) -> str:
    #     return self.cpu

    # @computed_field
    # def graphics_divice(self) -> str:
    #     return self.gpu

    # @computed_field
    # def system_mem(self) -> int:
    #     return self.memory

    # @computed_field
    # def graphics_mem(self) -> int:
    #     return self.gpu_memory

class StatsInfo(BaseModel):
    """使用的统计信息模型"""
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
    stat_time: int = Field(..., alias="mtime")
    created_at: int

    class Config:
        # 允许通过原始字段名和别名字段名访问
        populate_by_name = True
        # 允许别名
        allow_population_by_field_name = True