from typing import Dict, Any, Optional
from ..base import BaseExecutor


class ProcessCommands:
    """进程相关命令"""

    def __init__(self, executor: BaseExecutor):
        self.executor = executor

    def list_processes(self, grep_pattern: str = "") -> Dict[str, Any]:
        """列出进程"""
        if grep_pattern:
            command = f"ps aux | grep {grep_pattern} | grep -v grep"
        else:
            command = "ps aux | head -30"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def query_process(self, pid_or_name: str) -> Dict[str, Any]:
        """查询特定进程"""
        if pid_or_name.isdigit():
            command = f"ps -p {pid_or_name} -o pid,ppid,user,%cpu,%mem,cmd"
        else:
            command = f"ps aux | grep {pid_or_name} | grep -v grep"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def kill_process(self, pid: int, signal: int = 15) -> Dict[str, Any]:
        """终止进程（默认 SIGTERM）"""
        command = f"kill -{signal} {pid}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def force_kill_process(self, pid: int) -> Dict[str, Any]:
        """强制终止进程（SIGKILL）"""
        return self.kill_process(pid, signal=9)

    def list_ports(self) -> Dict[str, Any]:
        """列出监听端口"""
        command = "netstat -tlnp 2>/dev/null | head -20"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def query_port(self, port: int) -> Dict[str, Any]:
        """查询特定端口"""
        command = f"netstat -tlnp 2>/dev/null | grep :{port}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }
