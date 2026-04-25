from typing import Dict, Any, List, Optional
import json
from pathlib import Path


class ConversationHistory:
    """对话历史持久化"""

    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self):
        """从文件加载历史"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []

    def _save_history(self):
        """保存历史到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史失败: {e}")

    def add_entry(self, entry: Dict[str, Any]):
        """添加历史记录"""
        self.history.append(entry)
        self._save_history()

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取历史记录"""
        return self.history[-limit:]

    def clear_history(self):
        """清空历史"""
        self.history.clear()
        self._save_history()

    def search_history(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索历史"""
        results = []
        for entry in self.history:
            if keyword.lower() in str(entry).lower():
                results.append(entry)
        return results
