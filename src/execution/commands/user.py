from typing import Dict, Any
from ..base import BaseExecutor
from security import SecurityValidator


class UserCommands:
    """用户管理命令"""

    def __init__(self, executor: BaseExecutor):
        self.executor = executor
        self.security_validator = SecurityValidator(enable_secondary_confirmation=False)

    @staticmethod
    def _blocked_result(error: str) -> Dict[str, Any]:
        return {
            'success': False,
            'output': "",
            'error': error,
            'command': ""
        }

    def list_users(self) -> Dict[str, Any]:
        """列出所有用户"""
        command = "cat /etc/passwd | cut -d: -f1 | sort"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def create_user(self, username: str, create_home: bool = True, password: str = None) -> Dict[str, Any]:
        """创建用户"""
        is_safe, message = self.security_validator.validate_user_operation(username, "create")
        if not is_safe:
            return self._blocked_result(message)

        if create_home:
            command = f"useradd -m {username}"
        else:
            command = f"useradd {username}"

        # 如果提供了密码，设置密码
        if password:
            command += f" && echo '{username}:{password}' | chpasswd"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def delete_user(self, username: str, remove_home: bool = False) -> Dict[str, Any]:
        """删除用户"""
        is_safe, message = self.security_validator.validate_user_operation(username, "delete")
        if not is_safe:
            return self._blocked_result(message)

        # 检查用户是否被占用
        check_command = f"ps -ef | grep {username} | grep -v grep"
        check_result = self.executor.execute(check_command)

        if check_result.success and check_result.stdout.strip():
            # 用户被占用，先终止相关进程
            print("删除中...")

            # 首先尝试使用 pkill -u 强制终止所有用户进程（推荐方法）
            pkill_command = f"pkill -u {username}"
            pkill_result = self.executor.execute(pkill_command)

            if not pkill_result.success:
                # 如果pkill失败，尝试逐个终止进程
                pids = []
                for line in check_result.stdout.split('\n'):
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except ValueError:
                            continue

                if pids:
                    for pid in pids:
                        kill_command = f"kill -9 {pid}"
                        self.executor.execute(kill_command)

            # 等待进程完全终止
            import time
            time.sleep(2)

        # 执行用户删除
        if remove_home:
            command = f"userdel -r {username}"
        else:
            command = f"userdel {username}"

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """获取用户信息"""
        command = f"id {username}"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def modify_user(self, username: str, action: str, value: str = "") -> Dict[str, Any]:
        """修改用户"""
        if action == "add_group":
            command = f"usermod -aG {value} {username}"
        elif action == "remove_group":
            command = f"gpasswd -d {username} {value}"
        elif action == "shell":
            command = f"usermod -s {value} {username}"
        elif action == "home":
            command = f"usermod -d {value} {username}"
        else:
            return {
                'success': False,
                'output': "",
                'error': f"不支持的修改操作: {action}",
                'command': ""
            }

        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }

    def set_password(self, username: str, password: str) -> Dict[str, Any]:
        """设置用户密码"""
        command = f"echo '{username}:{password}' | chpasswd"
        result = self.executor.execute(command)

        return {
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr,
            'command': command
        }
