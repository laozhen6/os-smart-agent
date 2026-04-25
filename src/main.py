#!/usr/bin/env python3
"""
操作系统智能代理 - 主入口
"""

import os
import sys
import argparse
from pathlib import Path
import random
import string

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from config import Config
from intent import IntentParser
from execution import LocalExecutor, SSHExecutor, DiskCommands, FileCommands, ProcessCommands, UserCommands
from security import SecurityValidator
from conversation import ConversationManager, ConversationHistory
from feedback import ResponseFormatter
from cli import CLIInterface


class OSSmartAgent:
    """操作系统智能代理主类"""

    def __init__(self, config_path: str = None, mode: str = None,
                 host: str = None, port: int = None, username: str = None,
                 password: str = None, key_file: str = None):
        # 加载配置
        self.config = Config(config_path)

        # 确定执行模式
        self.mode = mode or self.config.execution_mode

        # 初始化执行引擎
        if self.mode == 'local':
            self.executor = LocalExecutor(timeout=self.config.execution_timeout)
        elif self.mode == 'ssh':
            ssh_config = self.config.ssh_config
            host = host or ssh_config.get('host')
            port = port or ssh_config.get('port', 22)
            username = username or ssh_config.get('username')
            password = password or ssh_config.get('password')
            key_file = key_file or ssh_config.get('key_file')

            if not host or not username:
                raise ValueError("SSH 模式需要 host 和 username 参数")

            self.executor = SSHExecutor(
                host=host,
                port=port,
                username=username,
                password=password,
                key_file=key_file,
                timeout=self.config.execution_timeout
            )
        else:
            raise ValueError(f"不支持的执行模式: {self.mode}")

        # 初始化命令封装
        self.disk_commands = DiskCommands(self.executor)
        self.file_commands = FileCommands(self.executor)
        self.process_commands = ProcessCommands(self.executor)
        self.user_commands = UserCommands(self.executor)

        # 初始化意图识别
        if not self.config.api_key:
            raise ValueError("未设置 SILICONFLOW_API_KEY 环境变量或配置文件")

        self.intent_parser = IntentParser(
            base_url=self.config.api_base_url,
            model=self.config.api_model,
            api_key=self.config.api_key
        )

        # 初始化安全验证器
        self.security_validator = SecurityValidator(
            enable_secondary_confirmation=self.config.enable_secondary_confirmation
        )

        # 初始化对话管理
        self.conversation_manager = ConversationManager()
        self.conversation_history = ConversationHistory()

        # 初始化响应格式化器
        self.formatter = ResponseFormatter()

        # 初始化 CLI 界面
        self.cli = CLIInterface()

    def generate_verification_code(self) -> str:
        """生成四字随机验证码"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(4))

    def verify_user_input(self, code: str) -> bool:
        """验证用户输入的验证码"""
        attempts = 3
        while attempts > 0:
            user_input = input(f"请输入验证码 ({code}): ").strip()
            if user_input == code:
                return True
            attempts -= 1
            if attempts > 0:
                print(f"验证码错误，还剩 {attempts} 次机会")
        return False

    def confirm_high_risk_operation(self, intent) -> bool:
        """确认高风险操作"""
        print(f"\n⚠️  警告：检测到高风险操作 (危险等级: {intent.risk_level.value})")
        print(f"操作说明: {intent.explanation}")
        print("此操作可能对系统造成重大影响，请谨慎操作。")

        # 生成验证码
        verification_code = self.generate_verification_code()
        print(f"请输入以下验证码以继续: {verification_code}")

        # 验证用户输入
        if not self.verify_user_input(verification_code):
            print("验证失败，操作已取消。")
            return False

        # 二次确认
        confirm = input("您确定要继续执行此操作吗？(y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消。")
            return False

        return True

    def get_user_password(self, username: str) -> str:
        """获取用户密码"""
        while True:
            password = input(f"请输入用户 {username} 的密码: ").strip()
            if password:
                return password
            print("密码不能为空，请重新输入。")

    def test_connection(self) -> bool:
        """测试连接"""
        success, message = self.executor.test_connection()
        if success:
            if self.mode == 'local':
                system_type = "本地系统"
            else:
                system_type = f"远程服务器 {self.config.ssh_config.get('host', '未知')}"
            self.cli.display_success(f"连接成功 - {system_type}")
        else:
            self.cli.display_error(message)
        return success

    def execute_intent(self, intent, context: dict = None) -> tuple:
        """执行意图并返回结果"""
        command = ""
        result = None

        try:
            # 根据意图类型执行相应命令
            if intent.intent.value == 'disk_query':
                mount_point = intent.parameters.get('mount_point', '')
                result = self.disk_commands.query_disk_usage(mount_point)
                command = result['command']

            elif intent.intent.value == 'disk_analyze':
                path = intent.parameters.get('path', '/')
                result = self.disk_commands.analyze_disk_space(path)
                command = result['command']

            elif intent.intent.value == 'file_search':
                path = intent.parameters.get('path', '.')
                pattern = intent.parameters.get('pattern', '')
                result = self.file_commands.search_files(path, pattern)
                command = result['command']

            elif intent.intent.value == 'file_create':
                path = intent.parameters.get('path', '')
                content = intent.parameters.get('content', '')
                result = self.file_commands.create_file(path, content)
                command = result['command']

            elif intent.intent.value == 'file_delete':
                path = intent.parameters.get('path', '')
                recursive = intent.parameters.get('recursive', False)
                result = self.file_commands.delete_file(path, recursive)
                command = result['command']

            elif intent.intent.value == 'file_modify':
                # 读取/列出文件
                path = intent.parameters.get('path', context.get('last_path', '')) if context else intent.parameters.get('path', '')
                result = self.file_commands.read_file(path)
                command = result['command']

            elif intent.intent.value == 'directory_create':
                path = intent.parameters.get('path', '')
                result = self.file_commands.create_directory(path)
                command = result['command']

            elif intent.intent.value == 'directory_query':
                path = intent.parameters.get('path', '.')
                result = self.file_commands.list_directory(path)
                command = result['command']

            elif intent.intent.value == 'process_list':
                pattern = intent.parameters.get('pattern', '')
                result = self.process_commands.list_processes(pattern)
                command = result['command']

            elif intent.intent.value == 'process_query':
                process = intent.parameters.get('process', '')
                result = self.process_commands.query_process(process)
                command = result['command']

            elif intent.intent.value == 'process_kill':
                process = intent.parameters.get('process', '')
                try:
                    pid = int(process)
                    result = self.process_commands.kill_process(pid)
                    command = result['command']
                except ValueError:
                    raise ValueError(f"无效的进程 ID: {process}")

            elif intent.intent.value == 'user_create':
                username = intent.parameters.get('user', '')

                # 检查参数中是否包含密码
                password = intent.parameters.get('password', '')
                if not password:
                    # 如果没有密码，询问用户
                    password = self.get_user_password(username)

                result = self.user_commands.create_user(username, password=password)
                command = result['command']

            elif intent.intent.value == 'user_delete':
                username = intent.parameters.get('user', '')
                print("删除中...")
                result = self.user_commands.delete_user(username)
                command = result['command']
                if result['success']:
                    print(f"用户 {username} 删除完成")

            elif intent.intent.value == 'user_modify':
                username = intent.parameters.get('user', '')
                action = intent.parameters.get('action', '')
                value = intent.parameters.get('value', '')
                result = self.user_commands.modify_user(username, action, value)
                command = result['command']

            elif intent.intent.value == 'user_query':
                username = intent.parameters.get('user', '')
                result = self.user_commands.get_user_info(username)
                command = result['command']

            elif intent.intent.value == 'port_query':
                port = intent.parameters.get('port', '')
                result = self.process_commands.query_port(int(port))
                command = result['command']

            elif intent.intent.value == 'system_info':
                command = "uname -a"
                exec_result = self.executor.execute(command)
                result = {
                    'success': exec_result.success,
                    'output': exec_result.stdout,
                    'error': exec_result.stderr,
                    'command': command
                }

            else:
                raise ValueError(f"不支持的意图: {intent.intent.value}")

            return command, result

        except Exception as e:
            return command, {
                'success': False,
                'output': '',
                'error': str(e),
                'command': command
            }

    def run(self):
        """运行智能代理"""
        # 显示欢迎信息
        self.cli.display_banner()

        # 测试连接
        if not self.test_connection():
            self.cli.display_error("无法连接到目标系统，请检查配置")
            return

        # 主循环
        while self.cli.is_running():
            # 获取用户输入
            user_input = self.cli.get_user_input()

            if not user_input:
                continue

            # 检查退出命令
            if self.cli.should_exit(user_input):
                self.cli.display_message("感谢使用，再见！")
                break

            # 检查帮助命令
            if self.cli.is_help_command(user_input):
                self.cli.display_message(self.formatter.format_help())
                continue

            # 检查清屏命令
            if self.cli.is_clear_command(user_input):
                self.cli.clear_screen()
                self.cli.display_banner()
                continue

            # 检查历史命令
            if self.cli.is_history_command(user_input):
                self.cli.display_message(self.conversation_manager.get_history_summary())
                continue

            # 解析意图
            self.cli.display_message(f"\n正在解析意图: {user_input}")
            intent = self.intent_parser.parse(user_input)

            # 增强意图（使用上下文）
            context = self.conversation_manager.get_context()
            intent = self.intent_parser.enhance_with_context(intent, context)

            # 验证参数
            valid, msg = self.intent_parser.validate_parameters(intent)
            if not valid:
                self.cli.display_error(msg)
                continue

            # 显示意图解析结果
            self.cli.display_message(f"识别意图: {intent.intent.value}")
            self.cli.display_message(f"风险等级: {intent.risk_level.value}")
            self.cli.display_message(f"说明: {intent.explanation}")
            self.cli.display_separator()

            # 安全检查
            should_block, block_reason = self.security_validator.should_block_operation(intent)
            if should_block:
                self.cli.display_error(block_reason)
                continue

            # 高风险操作二次确认
            if intent.risk_level.value == 'high':
                if not self.confirm_high_risk_operation(intent):
                    continue

            # 执行意图
            command, result = self.execute_intent(intent, context)

            # 显示执行结果
            if result['success']:
                response = self.formatter.format_success(intent, result, command)

                # 根据意图类型进行特殊格式化
                if intent.intent.value == 'disk_query':
                    response = self.formatter.format_disk_usage(result['output'])
                elif intent.intent.value == 'file_search':
                    response = self.formatter.format_file_search(result['output'])
                elif intent.intent.value == 'directory_query':
                    response = self.formatter.format_directory_listing(result['output'])
                elif intent.intent.value == 'process_list':
                    response = self.formatter.format_process_list(result['output'])

                self.cli.display_success(response)
            else:
                error_response = self.formatter.format_error(intent, {
                    'stdout': result['output'],
                    'stderr': result['error'],
                    'exit_code': -1
                }, command)
                self.cli.display_error(error_response)

            # 保存到对话历史
            self.conversation_manager.add_message(
                user_input=user_input,
                intent=intent,
                result=result,
                response=str(result['success'])
            )

            self.cli.display_separator()
            print()

        # 清理
        if self.mode == 'ssh':
            self.executor.close()


def main():
    """主函数"""
    # 交互式选择执行模式
    print("欢迎使用操作系统智能代理")
    print("请选择执行模式：")
    print("1. 本地部署")
    print("2. 远程连接")

    while True:
        choice = input("请输入选择 (1/2): ").strip()
        if choice == '1':
            mode = 'local'
            print("\n⚠️  警告：您选择了本地部署模式，所有操作将在当前系统执行。")
            break
        elif choice == '2':
            mode = 'ssh'
            print("\n⚠️  警告：您选择了远程连接模式，所有操作将在远程服务器执行。")
            break
        else:
            print("无效选择，请重新输入 1 或 2")

    parser = argparse.ArgumentParser(description='操作系统智能代理')
    parser.add_argument('--config', default=None,
                        help='配置文件路径')
    parser.add_argument('--host', default=None,
                        help='SSH 主机地址（SSH 模式）')
    parser.add_argument('--port', type=int, default=None,
                        help='SSH 端口（SSH 模式）')
    parser.add_argument('--user', default=None,
                        help='SSH 用户名（SSH 模式）')
    parser.add_argument('--password', default=None,
                        help='SSH 密码（SSH 模式）')
    parser.add_argument('--key-file', default=None,
                        help='SSH 私钥文件路径（SSH 模式）')

    args = parser.parse_args()

    try:
        agent = OSSmartAgent(
            config_path=args.config,
            mode=mode,
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
            key_file=args.key_file
        )
        agent.run()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
