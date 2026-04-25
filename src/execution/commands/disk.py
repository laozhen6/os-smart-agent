from typing import Dict, Any, Optional
from ..base import BaseExecutor


class DiskCommands:
    """磁盘相关命令"""

    def __init__(self, executor: BaseExecutor):
        self.executor = executor

    def query_disk_usage(self, mount_point: str = "") -> Dict[str, Any]:
        """查询磁盘使用情况"""
        if mount_point:
            command = f"df -h {mount_point}"
        else:
            command = "df -h"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def analyze_disk_space(self, path: str = "/") -> Dict[str, Any]:
        """分析磁盘空间（按目录大小排序）"""
        command = f"du -sh {path}/* 2>/dev/null | sort -hr | head -20"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def check_inode_usage(self, path: str = "/") -> Dict[str, Any]:
        """检查 inode 使用情况"""
        command = f"df -i {path}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }
