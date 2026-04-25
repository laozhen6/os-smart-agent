import sys
import os


class CLIInterface:
    """命令行交互界面"""

    def __init__(self, history_file: str = ".cli_history"):
        self.history_file = history_file
        self.running = True

    def get_user_input(self, prompt_text: str = "您 > ") -> str:
        """获取用户输入"""
        try:
            user_input = input(prompt_text).strip()
            return user_input
        except KeyboardInterrupt:
            print("\n\n输入已取消")
            return ""
        except EOFError:
            self.running = False
            return "exit"

    def get_confirmation(self) -> bool:
        """获取用户确认"""
        try:
            response = input("确认执行? (y/N): ").strip().lower()
            return response == 'y' or response == 'yes'
        except (KeyboardInterrupt, EOFError):
            return False

    def display_message(self, message: str):
        """显示消息"""
        print(message)

    def display_error(self, error: str):
        """显示错误"""
        print(f"错误: {error}", file=sys.stderr)

    def display_warning(self, warning: str):
        """显示警告"""
        print(f"警告: {warning}")

    def display_success(self, success: str):
        """显示成功消息"""
        print(f"成功: {success}")

    def display_separator(self):
        """显示分隔线"""
        print("-" * 60)

    def clear_screen(self):
        """清屏"""
        print("\n" * 50)

    def display_banner(self):
        """显示欢迎横幅"""
        self.display_separator()
        print("操作系统智能代理")
        print("通过自然语言管理您的 Linux 服务器")
        self.display_separator()
        print("输入 'help' 查看可用命令")
        print("输入 'exit' 或 'quit' 退出")
        self.display_separator()
        print()

    def is_running(self) -> bool:
        """检查是否继续运行"""
        return self.running

    def stop(self):
        """停止运行"""
        self.running = False

    def should_exit(self, user_input: str) -> bool:
        """检查是否应该退出"""
        return user_input.lower() in ['exit', 'quit', 'q', 'bye']

    def is_help_command(self, user_input: str) -> bool:
        """检查是否是帮助命令"""
        return user_input.lower() in ['help', 'h', '?']

    def is_clear_command(self, user_input: str) -> bool:
        """检查是否是清屏命令"""
        return user_input.lower() in ['clear', 'cls', 'c']

    def is_history_command(self, user_input: str) -> bool:
        """检查是否是历史命令"""
        return user_input.lower() == 'history'