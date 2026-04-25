import re
from typing import Tuple, List
from .rules import (
    RISKY_PATHS,
    RISKY_COMMANDS,
    CRITICAL_FILES,
    PROTECTED_USERS,
    ILLEGAL_USERNAMES,
    DANGEROUS_USER_TOKENS,
)


class RiskAnalyzer:
    """风险分析器"""

    @staticmethod
    def analyze_command(command: str) -> Tuple[str, str]:
        """
        分析命令风险等级
        返回: (risk_level, reason)
        risk_level: 'low', 'medium', 'high'
        """
        # 检查高风险命令模式
        for risky_cmd in RISKY_COMMANDS:
            if risky_cmd in command:
                return 'high', f'包含高风险命令模式: {risky_cmd}'

        # 检查系统目录操作
        for path in RISKY_PATHS:
            if path in command and ('rm' in command or 'dd' in command or 'mkfs' in command):
                return 'high', f'涉及系统目录操作: {path}'

        # 检查关键文件修改
        for file_path in CRITICAL_FILES:
            if file_path in command and ('>' in command or 'rm' in command or 'mv' in command):
                return 'high', f'涉及关键配置文件: {file_path}'

        # 检查批量删除操作
        if 'rm -rf' in command and '*' in command:
            return 'high', '包含批量删除操作'

        # 中等风险：删除文件
        if 'rm' in command and not 'rm -rf /' in command:
            return 'medium', '文件删除操作'

        # 中等风险：用户修改
        if 'usermod' in command or 'chmod' in command:
            return 'medium', '用户或权限修改'

        # 低风险：查询操作
        return 'low', '查询或创建操作'

    @staticmethod
    def analyze_path(path: str, operation: str) -> Tuple[str, str]:
        """
        分析路径操作风险
        operation: 'read', 'write', 'delete', 'modify'
        """
        if not path:
            return 'low', '路径未指定'

        # 检查系统路径
        for risky_path in RISKY_PATHS:
            if path.startswith(risky_path) and path != risky_path:
                if operation in ['delete', 'modify']:
                    return 'high', f'涉及系统路径: {path}'
                elif operation == 'write':
                    return 'medium', f'写入系统路径: {path}'

        # 检查关键文件
        if path in CRITICAL_FILES and operation in ['delete', 'modify', 'write']:
            return 'high', f'关键配置文件: {path}'

        return 'low', '路径操作风险低'

    @staticmethod
    def analyze_user_operation(username: str, operation: str) -> Tuple[str, str]:
        """
        分析用户操作风险
        operation: 'create', 'delete', 'modify'
        """
        if not username:
            return 'low', '用户名未指定'

        for token in DANGEROUS_USER_TOKENS:
            if token in username:
                return 'high', f'用户名包含危险指令片段: {token}'

        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]{0,31}', username):
            return 'high', f'非法用户名: {username}'

        # 检查系统用户
        for sys_user in PROTECTED_USERS:
            if username.startswith(sys_user):
                if operation == 'delete':
                    return 'high', f'系统用户: {username}'
                elif operation == 'modify':
                    return 'medium', f'修改系统用户: {username}'
                elif operation == 'create':
                    return 'high', f'受保护用户名: {username}'

        # 检查 root 用户
        if username == 'root':
            if operation == 'delete':
                return 'high', 'root 用户不能删除'
            elif operation == 'modify':
                return 'high', 'root 用户修改操作'
            elif operation == 'create':
                return 'high', 'root 用户不能创建'

        if operation == 'create' and username.lower() in ILLEGAL_USERNAMES:
            return 'high', f'禁止创建保留用户名: {username}'

        # 删除操作风险
        if operation == 'delete':
            return 'medium', '删除用户操作'

        return 'low', '用户操作风险低'

    @staticmethod
    def analyze_process_operation(process: str, operation: str) -> Tuple[str, str]:
        """
        分析进程操作风险
        operation: 'query', 'kill'
        """
        if operation == 'kill':
            # 检查系统关键进程
            critical_processes = ['init', 'systemd', 'kernel', 'sshd']
            for proc in critical_processes:
                if proc in process.lower():
                    return 'high', f'关键系统进程: {process}'

            return 'medium', '终止进程操作'

        return 'low', '进程查询操作'

    @staticmethod
    def get_risk_description(risk_level: str, reason: str) -> str:
        """获取风险描述"""
        descriptions = {
            'low': '低风险操作，可以安全执行',
            'medium': '中等风险操作，建议仔细检查',
            'high': '高风险操作，强烈建议进行二次确认'
        }
        return f"{descriptions.get(risk_level, '未知风险')} - {reason}"

    @staticmethod
    def should_require_confirmation(risk_level: str, enable_secondary: bool) -> bool:
        """判断是否需要二次确认"""
        if not enable_secondary:
            return False
        return risk_level in ['medium', 'high']
