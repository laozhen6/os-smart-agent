from typing import Tuple, Optional
from .analyzer import RiskAnalyzer
from intent.schemas import Intent


class SecurityValidator:
    """安全验证器"""

    def __init__(self, enable_secondary_confirmation: bool = True):
        self.enable_secondary_confirmation = enable_secondary_confirmation
        self.analyzer = RiskAnalyzer()

    def validate_intent(self, intent: Intent, command: str = "") -> Tuple[bool, str]:
        """
        验证意图是否安全
        返回: (is_safe, message)
        """
        # 检查意图类型和风险等级
        if intent.risk_level.value == 'high':
            if not self.enable_secondary_confirmation:
                return False, f"高风险操作被禁用: {intent.explanation}"
            return False, f"需要二次确认: {intent.explanation}"

        # 如果提供了命令，进行命令级分析
        if command:
            risk_level, reason = self.analyzer.analyze_command(command)
            if risk_level == 'high':
                return False, f"检测到高风险命令: {reason}"
            elif risk_level == 'medium':
                if not self.enable_secondary_confirmation:
                    return True, f"中等风险操作: {reason}"
                return False, f"需要确认: {reason}"

        return True, "操作安全"

    def validate_path_operation(self, path: str, operation: str) -> Tuple[bool, str]:
        """验证路径操作"""
        risk_level, reason = self.analyzer.analyze_path(path, operation)
        if risk_level == 'high':
            return False, f"高风险路径操作: {reason}"
        elif risk_level == 'medium' and self.enable_secondary_confirmation:
            return False, f"需要确认: {reason}"
        return True, f"路径操作安全: {reason}"

    def validate_user_operation(self, username: str, operation: str) -> Tuple[bool, str]:
        """验证用户操作"""
        risk_level, reason = self.analyzer.analyze_user_operation(username, operation)
        if risk_level == 'high':
            return False, f"高风险用户操作: {reason}"
        elif risk_level == 'medium' and self.enable_secondary_confirmation:
            return False, f"需要确认: {reason}"
        return True, f"用户操作安全: {reason}"

    def validate_process_operation(self, process: str, operation: str) -> Tuple[bool, str]:
        """验证进程操作"""
        risk_level, reason = self.analyzer.analyze_process_operation(process, operation)
        if risk_level == 'high':
            return False, f"高风险进程操作: {reason}"
        elif risk_level == 'medium' and self.enable_secondary_confirmation:
            return False, f"需要确认: {reason}"
        return True, f"进程操作安全: {reason}"

    def should_block_operation(self, intent: Intent, command: str = "") -> Tuple[bool, str]:
        """
        判断是否应该阻止操作
        返回: (should_block, reason)
        """
        # 严格阻止某些高风险操作
        if 'root' in str(intent.parameters.get('user', '')) and intent.intent.value in ['user_delete']:
            return True, "禁止删除 root 用户"

        if '/etc/passwd' in command and '>' in command:
            return True, "禁止覆盖 /etc/passwd 文件"

        return False, ""

    def get_security_summary(self, intent: Intent, command: str = "") -> str:
        """获取安全摘要信息"""
        summary_parts = []

        # 意图风险
        summary_parts.append(f"意图风险等级: {intent.risk_level.value}")

        # 如果有命令，分析命令风险
        if command:
            cmd_risk, cmd_reason = self.analyzer.analyze_command(command)
            summary_parts.append(f"命令风险等级: {cmd_risk}")
            if cmd_risk != 'low':
                summary_parts.append(f"原因: {cmd_reason}")

        return "\n".join(summary_parts)
