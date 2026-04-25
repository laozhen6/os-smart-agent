from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


class IntentType(str, Enum):
    """意图类型枚举"""
    DISK_QUERY = "disk_query"          # 磁盘查询
    DISK_ANALYZE = "disk_analyze"      # 磁盘分析
    FILE_SEARCH = "file_search"        # 文件搜索
    FILE_CREATE = "file_create"        # 文件创建
    FILE_DELETE = "file_delete"        # 文件删除
    FILE_MODIFY = "file_modify"        # 文件修改
    DIRECTORY_CREATE = "directory_create"  # 目录创建
    DIRECTORY_QUERY = "directory_query"  # 目录查询
    PROCESS_LIST = "process_list"      # 进程列表
    PROCESS_QUERY = "process_query"    # 进程查询
    PROCESS_KILL = "process_kill"      # 进程终止
    USER_CREATE = "user_create"        # 用户创建
    USER_DELETE = "user_delete"        # 用户删除
    USER_MODIFY = "user_modify"        # 用户修改
    USER_QUERY = "user_query"          # 用户查询
    PORT_QUERY = "port_query"          # 端口查询
    SYSTEM_INFO = "system_info"        # 系统信息
    UNKNOWN = "unknown"                # 未知意图


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Intent(BaseModel):
    """意图解析结果"""
    intent: IntentType
    risk_level: RiskLevel
    parameters: Dict[str, Any]
    explanation: str
    confidence: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "disk_query",
                "risk_level": "low",
                "parameters": {"mount_point": "/"},
                "explanation": "查询根目录的磁盘使用情况",
                "confidence": 0.95
            }
        }


class CommandTemplate(BaseModel):
    """命令模板"""
    intent: IntentType
    command_template: str
    required_params: list[str]
    optional_params: list[str]
