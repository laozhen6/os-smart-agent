from typing import Dict, Any, List
from execution.base import ExecutionResult
from intent.schemas import Intent


class ResponseFormatter:
    """响应格式化器"""

    @staticmethod
    def format_success(intent: Intent, result: dict, command: str = "") -> str:
        """格式化成功响应"""
        lines = []
        lines.append("✓ 操作执行成功\n")

        # 添加执行说明
        if intent.explanation:
            lines.append(f"执行说明: {intent.explanation}\n")

        # 添加命令
        if command:
            lines.append(f"执行命令: {command}\n")

        # 格式化输出结果
        if 'stdout' in result and result['stdout']:
            lines.append("执行结果:")
            formatted_output = ResponseFormatter._format_output(result['stdout'])
            lines.append(formatted_output)

        return "\n".join(lines)

    @staticmethod
    def format_error(intent: Intent, result: dict, command: str = "") -> str:
        """格式化错误响应"""
        lines = []
        lines.append("✗ 操作执行失败\n")

        # 添加错误说明
        if 'stderr' in result and result['stderr']:
            stderr = result['stderr']
            lines.append(f"错误信息: {stderr}\n")

            # 检查是否是用户被占用错误
            if "is currently used by process" in stderr:
                lines.append("⚠️  检测到用户被占用，系统正在处理...\n")
                lines.append("系统已自动尝试终止相关进程并删除用户。\n")
                lines.append("如果仍有问题，请手动执行以下命令：\n")
                lines.append("1. 终止占用进程: kill -9 <进程ID>\n")
                lines.append("2. 强制终止用户所有进程: pkill -u <用户名>\n")
                lines.append("3. 删除用户: userdel -r <用户名>\n")
            else:
                lines.append(f"错误信息: {stderr}\n")
        else:
            lines.append(f"错误信息: 未知错误 (退出码: {result.get('exit_code', -1)})\n")

        # 添加命令
        if command:
            lines.append(f"执行命令: {command}\n")

        # 添加建议
        lines.append("建议: 请检查参数是否正确，或联系系统管理员")

        return "\n".join(lines)

    @staticmethod
    def format_risk_warning(risk_level: str, reason: str, command: str = "") -> str:
        """格式化风险警告"""
        lines = []

        if risk_level == 'high':
            lines.append("⚠️  高风险操作警告\n")
            lines.append(f"风险原因: {reason}\n")
            lines.append("此操作可能对系统造成严重影响，请谨慎操作！\n")
        elif risk_level == 'medium':
            lines.append("⚠️  中等风险操作\n")
            lines.append(f"风险原因: {reason}\n")
            lines.append("请确认操作正确性后继续\n")

        if command:
            lines.append(f"即将执行的命令: {command}")

        return "\n".join(lines)

    @staticmethod
    def format_confirmation_request(operation: str, details: str = "") -> str:
        """格式化确认请求"""
        lines = []
        lines.append("需要您的确认\n")
        lines.append(f"操作: {operation}\n")
        if details:
            lines.append(f"详情: {details}\n")
        lines.append("输入 'y' 确认，其他任何输入取消")

        return "\n".join(lines)

    @staticmethod
    def format_disk_usage(output: str) -> str:
        """格式化磁盘使用情况输出"""
        if not output:
            return "无输出"

        lines = output.split('\n')
        if len(lines) < 2:
            return output

        # 解析并总结
        summary = []
        total_size = 0
        total_used = 0
        total_available = 0

        for line in lines[1:]:  # 跳过标题行
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                try:
                    size = ResponseFormatter._parse_size(parts[1])
                    used = ResponseFormatter._parse_size(parts[2])
                    available = ResponseFormatter._parse_size(parts[3])
                    total_size += size
                    total_used += used
                    total_available += available
                except:
                    pass

        if total_size > 0:
            usage_percent = (total_used / total_size) * 100
            summary.append(f"磁盘总容量: {ResponseFormatter._format_size(total_size)}")
            summary.append(f"已使用: {ResponseFormatter._format_size(total_used)} ({usage_percent:.1f}%)")
            summary.append(f"剩余空间: {ResponseFormatter._format_size(total_available)}")

        return "\n".join(summary) + "\n\n" + output

    @staticmethod
    def format_file_search(output: str) -> str:
        """格式化文件搜索结果"""
        if not output:
            return "未找到匹配的文件"

        lines = output.split('\n')
        file_count = len([line for line in lines if line.strip()])

        result = f"找到 {file_count} 个文件:\n"
        result += output

        return result

    @staticmethod
    def format_process_list(output: str) -> str:
        """格式化进程列表"""
        if not output:
            return "无进程信息"

        lines = output.split('\n')
        process_count = len([line for line in lines[1:] if line.strip()])  # 排除标题

        result = f"显示 {process_count} 个进程:\n"
        result += output

        return result

    @staticmethod
    def format_directory_listing(output: str) -> str:
        """格式化目录查询结果"""
        if not output:
            return "无目录信息"

        lines = [line for line in output.split('\n') if line.strip()]
        if not lines:
            return "无目录信息"

        location = lines[0]
        listing = "\n".join(lines[1:])

        result = f"目录位置: {location}"
        if listing:
            result += f"\n\n目录内容:\n{listing}"

        return result

    @staticmethod
    def _format_output(output: str) -> str:
        """格式化输出文本"""
        if not output:
            return ""

        lines = output.split('\n')
        if len(lines) > 20:
            result = "\n".join(lines[:20])
            result += f"\n... (还有 {len(lines) - 20} 行，使用 'more' 查看更多)"
            return result
        return output

    @staticmethod
    def _parse_size(size_str: str) -> float:
        """解析大小字符串为 GB"""
        if not size_str or size_str == '-':
            return 0.0

        size_str = size_str.upper()
        if size_str.endswith('G'):
            return float(size_str[:-1])
        elif size_str.endswith('M'):
            return float(size_str[:-1]) / 1024
        elif size_str.endswith('T'):
            return float(size_str[:-1]) * 1024
        else:
            return 0.0

    @staticmethod
    def _format_size(size_gb: float) -> str:
        """格式化大小为易读字符串"""
        if size_gb >= 1024:
            return f"{size_gb / 1024:.2f} TB"
        elif size_gb >= 1:
            return f"{size_gb:.2f} GB"
        elif size_gb >= 0.001:
            return f"{size_gb * 1024:.2f} MB"
        else:
            return f"{size_gb * 1024 * 1024:.2f} KB"

    @staticmethod
    def format_help() -> str:
        """格式化帮助信息"""
        help_text = """
操作系统智能代理 - 帮助信息

支持的操作:
  磁盘管理:
    - 查询磁盘使用情况: "查看磁盘" / "查询磁盘使用"
    - 分析磁盘空间: "分析 /var 目录占用"

  文件操作:
    - 搜索文件: "查找 /var/log 下的 .log 文件"
    - 创建文件: "创建文件 /tmp/test.txt"
    - 删除文件: "删除 /tmp/test.txt"
    - 查看文件: "读取 /var/log/syslog"

  进程管理:
    - 查看进程: "列出所有进程" / "查看 nginx 进程"
    - 终止进程: "停止进程 1234"
    - 查看端口: "查看 80 端口"

  用户管理:
    - 创建用户: "创建用户 testuser"
    - 删除用户: "删除用户 testuser"
    - 查看用户: "查看用户信息"

  系统信息:
    - 查看系统信息: "系统信息" / "系统状态"

其他命令:
  - 输入 'help' 查看此帮助
  - 输入 'history' 查看对话历史
  - 输入 'clear' 清屏
  - 输入 'exit' 或 'quit' 退出

注意事项:
  - 高风险操作会提示确认
  - 可以使用上下文，如"查看其详情"引用上一次操作
"""
        return help_text

    @staticmethod
    def format_system_info(output: str) -> str:
        """格式化系统信息"""
        info = {
            '系统': output.split('\n')[0] if output else '未知',
            '提示': '使用 "help" 查看更多命令'
        }

        result = "系统信息:\n"
        for key, value in info.items():
            result += f"  {key}: {value}\n"

        return result
