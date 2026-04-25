import subprocess
from typing import Tuple
from .base import BaseExecutor, ExecutionResult


class LocalExecutor(BaseExecutor):
    """本地执行引擎"""

    def execute(self, command: str) -> ExecutionResult:
        """在本地执行命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"命令执行超时（{self.timeout}秒）",
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def execute_with_input(self, command: str, input_text: str) -> ExecutionResult:
        """执行需要输入的命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                input=input_text,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"命令执行超时（{self.timeout}秒）",
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def test_connection(self) -> Tuple[bool, str]:
        """测试连接（本地直接返回成功）"""
        try:
            result = self.execute("echo 'test'")
            if result.success:
                return True, "本地连接正常"
            else:
                return False, "本地命令执行失败"
        except Exception as e:
            return False, f"本地连接测试失败: {str(e)}"
