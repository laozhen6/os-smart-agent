from typing import Dict, Any, List, Optional
from datetime import datetime


class ConversationManager:
    """对话管理器"""

    def __init__(self, max_history: int = 50):
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.max_history = max_history

    def add_message(self, user_input: str, intent: Any, result: Any, response: str):
        """添加对话消息到历史"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent': intent,
            'result': result,
            'response': response
        }
        self.history.append(message)

        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # 更新上下文
        self._update_context(intent, result)

    def _update_context(self, intent: Any, result: Any):
        """更新对话上下文"""
        # 保存路径信息
        if hasattr(intent, 'parameters') and 'path' in intent.parameters:
            if intent.parameters['path']:
                self.context['last_path'] = intent.parameters['path']

        # 保存用户信息
        if hasattr(intent, 'parameters') and 'user' in intent.parameters:
            if intent.parameters['user']:
                self.context['last_user'] = intent.parameters['user']

        # 保存进程信息
        if hasattr(intent, 'parameters') and 'process' in intent.parameters:
            if intent.parameters['process']:
                self.context['last_process'] = intent.parameters['process']

        # 保存最后的结果类型
        if hasattr(intent, 'intent'):
            self.context['last_intent'] = intent.intent.value

    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        return self.context.copy()

    def get_recent_history(self, count: int = 5) -> List[Dict[str, Any]]:
        """获取最近的对话历史"""
        return self.history[-count:] if self.history else []

    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
        self.context.clear()

    def get_history_summary(self) -> str:
        """获取对话历史摘要"""
        if not self.history:
            return "暂无对话历史"

        summary = f"对话历史 ({len(self.history)} 条):\n"
        for i, msg in enumerate(self.history[-10:], 1):
            timestamp = msg['timestamp'].split('T')[1].split('.')[0]
            summary += f"{i}. [{timestamp}] {msg['user_input']}\n"

        return summary

    def find_similar_operations(self, intent_type: str) -> List[Dict[str, Any]]:
        """查找相似的操作历史"""
        similar = []
        for msg in self.history:
            if hasattr(msg['intent'], 'intent') and msg['intent'].intent.value == intent_type:
                similar.append(msg)
        return similar

    def get_context_hint(self) -> str:
        """获取上下文提示"""
        hints = []
        if 'last_path' in self.context:
            hints.append(f"上次路径: {self.context['last_path']}")
        if 'last_user' in self.context:
            hints.append(f"上次用户: {self.context['last_user']}")
        if 'last_process' in self.context:
            hints.append(f"上次进程: {self.context['last_process']}")

        return " | ".join(hints) if hints else "无上下文信息"
