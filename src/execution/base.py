from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class ExecutionResult:
    """执行结果"""
    def __init__(self, success: bool, stdout: str, stderr: str, exit_code: int = 0):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code
        }


class BaseExecutor(ABC):
    """执行引擎基类"""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    @abstractmethod
    def execute(self, command: str) -> ExecutionResult:
        """执行命令"""
        pass

    @abstractmethod
    def execute_with_input(self, command: str, input_text: str) -> ExecutionResult:
        """执行需要输入的命令"""
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """测试连接"""
        pass

    def safe_execute(self, command: str) -> Tuple[bool, ExecutionResult]:
        """安全执行命令（带错误处理）"""
        try:
            result = self.execute(command)
            return result.success, result
        except Exception as e:
            error_result = ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )
            return False, error_result
