import os
from typing import Dict, Any, Optional, List
from ..base import BaseExecutor


class FileCommands:
    """文件相关命令"""

    def __init__(self, executor: BaseExecutor):
        self.executor = executor

    def search_files(self, path: str, pattern: str = "", file_type: str = "f") -> Dict[str, Any]:
        """搜索文件"""
        if pattern:
            find_command = f"find {path} -name '{pattern}' -type {file_type} 2>/dev/null"
        else:
            find_command = f"find {path} -type {file_type} 2>/dev/null | head -50"

        # 搜索全系统时，find 遇到无权限目录通常会返回 1；这类部分可见结果应视为成功。
        command = f"{find_command}; rc=$?; [ $rc -eq 0 ] || [ $rc -eq 1 ]"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """创建文件"""
        if content:
            # 使用 cat 创建带内容的文件
            command = f"cat > {path} << 'EOF'\n{content}\nEOF"
        else:
            command = f"touch {path}"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def create_directory(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        command = f"mkdir -p {path}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def delete_file(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """删除文件"""
        if recursive:
            command = f"rm -rf {path}"
        else:
            command = f"rm -f {path}"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def get_file_info(self, path: str) -> Dict[str, Any]:
        """获取文件详细信息"""
        command = f"ls -lah {path}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def read_file(self, path: str, lines: int = 50) -> Dict[str, Any]:
        """读取文件内容"""
        command = f"head -{lines} {path}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def list_directory(self, path: str = ".", detail: bool = True) -> Dict[str, Any]:
        """列出目录内容"""
        if detail:
            command = f"cd {path} 2>/dev/null && pwd && ls -lah ."
        else:
            command = f"ls {path}"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }
