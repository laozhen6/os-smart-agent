import paramiko
import time
from typing import Tuple, Optional
from .base import BaseExecutor, ExecutionResult


class SSHExecutor(BaseExecutor):
    """SSH 远程执行引擎"""

    def __init__(self, host: str, port: int, username: str, password: Optional[str] = None,
                 key_file: Optional[str] = None, timeout: int = 300):
        super().__init__(timeout)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client: Optional[paramiko.SSHClient] = None
        self._connect()

    def _connect(self):
        """建立 SSH 连接"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.key_file:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_file,
                    timeout=10
                )
            elif self.password:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            else:
                raise ValueError("必须提供 password 或 key_file")
        except Exception as e:
            raise ConnectionError(f"SSH 连接失败: {str(e)}")

    def reconnect(self, max_retries: int = 3) -> bool:
        """重新连接"""
        for i in range(max_retries):
            try:
                if self.client:
                    self.client.close()
                self._connect()
                return True
            except Exception:
                if i < max_retries - 1:
                    time.sleep(2 ** i)  # 指数退避
                else:
                    return False
        return False

    def execute(self, command: str) -> ExecutionResult:
        """通过 SSH 执行命令"""
        if not self.client or not self.client.get_transport() or not self.client.get_transport().is_active():
            if not self.reconnect():
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="SSH 连接断开且重连失败",
                    exit_code=-1
                )

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
            exit_code = stdout.channel.recv_exit_status()

            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')

            return ExecutionResult(
                success=exit_code == 0,
                stdout=output,
                stderr=error,
                exit_code=exit_code
            )
        except paramiko.SSHException as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"SSH 执行错误: {str(e)}",
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
        """通过 SSH 执行需要输入的命令"""
        if not self.client or not self.client.get_transport() or not self.client.get_transport().is_active():
            if not self.reconnect():
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="SSH 连接断开且重连失败",
                    exit_code=-1
                )

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
            stdin.write(input_text)
            stdin.close()
            exit_code = stdout.channel.recv_exit_status()

            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')

            return ExecutionResult(
                success=exit_code == 0,
                stdout=output,
                stderr=error,
                exit_code=exit_code
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def test_connection(self) -> Tuple[bool, str]:
        """测试 SSH 连接"""
        try:
            if not self.client or not self.client.get_transport() or not self.client.get_transport().is_active():
                self.reconnect()

            result = self.execute("echo 'SSH connection test'")
            if result.success:
                return True, f"SSH 连接到 {self.host}:{self.port} 正常"
            else:
                return False, f"SSH 连接测试失败: {result.stderr}"
        except Exception as e:
            return False, f"SSH 连接测试失败: {str(e)}"

    def close(self):
        """关闭 SSH 连接"""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
