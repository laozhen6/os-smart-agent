#!/usr/bin/env python3
"""
操作系统智能代理测试脚本
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from intent import IntentParser
from execution import LocalExecutor
from security import SecurityValidator
from conversation import ConversationManager
from feedback import ResponseFormatter


def test_intent_parsing():
    """测试意图解析"""
    print("测试意图解析...")

    config = Config()
    parser = IntentParser(
        base_url=config.api_base_url,
        model=config.api_model,
        api_key=config.api_key
    )

    test_cases = [
        "查询磁盘使用情况",
        "查找 /var/log 下的 .log 文件",
        "列出所有运行中的进程",
        "创建用户 testuser",
        "删除用户 testuser",
        "查看 80 端口",
        "系统信息"
    ]

    for test_case in test_cases:
        print(f"\n测试输入: {test_case}")
        intent = parser.parse(test_case)
        print(f"  意图: {intent.intent.value}")
        print(f"  风险等级: {intent.risk_level.value}")
        print(f"  说明: {intent.explanation}")
        print(f"  参数: {intent.parameters}")


def test_local_execution():
    """测试本地执行"""
    print("\n测试本地执行引擎...")

    executor = LocalExecutor(timeout=10)

    commands = [
        "echo '测试本地执行'",
        "df -h",
        "ls -la /tmp",
        "ps aux | head -5"
    ]

    for cmd in commands:
        print(f"\n执行命令: {cmd}")
        result = executor.execute(cmd)
        print(f"  成功: {result.success}")
        if result.stdout:
            print(f"  输出: {result.stdout[:100]}...")


def test_security_validation():
    """测试安全验证"""
    print("\n测试安全验证...")

    validator = SecurityValidator(enable_secondary_confirmation=True)

    test_cases = [
        ("删除 /etc/passwd", "high"),
        ("删除 /tmp/test.txt", "medium"),
        ("查询磁盘使用", "low"),
        ("创建用户 testuser", "medium")
    ]

    for command, expected_risk in test_cases:
        risk_level, reason = SecurityValidator.analyze_command(command)
        print(f"\n命令: {command}")
        print(f"  风险等级: {risk_level} (预期: {expected_risk})")
        print(f"  原因: {reason}")


def test_conversation_manager():
    """测试对话管理"""
    print("\n测试对话管理...")

    manager = ConversationManager()

    test_inputs = [
        ("查询磁盘使用", "disk_query", "低风险", {"mount_point": "/"}),
        ("查找 /var/log", "file_search", "低风险", {"path": "/var/log", "pattern": "*.log"}),
        ("创建用户 test", "user_create", "中等风险", {"user": "test"})
    ]

    for user_input, intent_type, risk_level, params in test_inputs:
        intent = type('Intent', (), {
            'intent': type('IntentType', (), {'value': intent_type}),
            'risk_level': type('RiskLevel', (), {'value': risk_level}),
            'parameters': params,
            'explanation': f"测试 {intent_type} 操作"
        })

        result = {'success': True, 'output': '测试输出', 'error': '', 'command': 'echo test'}

        manager.add_message(user_input, intent, result, "成功")

    print(f"对话历史: {len(manager.get_recent_history())} 条")
    print(f"上下文: {manager.get_context()}")


def main():
    """主测试函数"""
    print("操作系统智能代理 - 测试脚本")
    print("=" * 50)

    try:
        # 检查 API Key
        if not os.getenv('SILICONFLOW_API_KEY'):
            print("警告: 未设置 SILICONFLOW_API_KEY 环境变量")
            print("请设置环境变量: export SILICONFLOW_API_KEY=your_api_key")
            return

        # 运行测试
        test_intent_parsing()
        test_local_execution()
        test_security_validation()
        test_conversation_manager()

        print("\n" + "=" * 50)
        print("所有测试完成！")

    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()