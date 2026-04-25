import json
import os
import re
from typing import Optional, Dict, Any
from openai import OpenAI
from openai import APIError

from .schemas import IntentType, RiskLevel, Intent


class IntentParser:
    """意图识别解析器"""

    def __init__(self, base_url: str, model: str, api_key: str):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个 Linux 系统管理专家和意图识别助手。你的任务是分析用户的自然语言指令，识别其意图、风险等级和相关参数。

请分析用户的指令，返回 JSON 格式的结果，包含以下字段：
- intent: 意图类型（从以下选项中选择）
  * disk_query - 查询磁盘使用情况
  * disk_analyze - 分析磁盘详细情况
  * file_search - 搜索文件或目录
  * file_create - 创建文件
  * file_delete - 删除文件
  * file_modify - 修改文件
  * directory_create - 创建目录
  * directory_query - 查询目录
  * process_list - 列出进程
  * process_query - 查询特定进程
  * process_kill - 终止进程
  * user_create - 创建用户
  * user_delete - 删除用户
  * user_modif - 修改用户
  * user_query - 查询用户信息
  * port_query - 查询端口状态
  * system_info - 查询系统信息
  * unknown - 无法识别

- risk_level: 风险等级（low/medium/high）
  * low: 查询类操作
  * medium: 创建文件、修改配置
  * high: 删除文件、删除用户、终止进程、修改系统配置

- parameters: 参数字典，包含提取的关键参数
  * path: 文件路径
  * user: 用户名
  * process: 进程名或PID
  * port: 端口号
  * mount_point: 挂载点
  * content: 文件内容
  * pattern: 搜索模式

- explanation: 对意图和执行计划的中文说明
- confidence: 置信度（0-1之间的浮点数）

只返回 JSON 格式，不要包含其他文字。"""

    def _simple_parse(self, user_input: str) -> tuple:
        """简单解析：基于关键词匹配"""
        input_lower = user_input.lower()

        # 磁盘查询
        if any(keyword in input_lower for keyword in ['磁盘', '硬盘', 'disk', '空间', 'space', '使用情况']):
            return IntentType.DISK_QUERY, {}, "查询磁盘使用情况"

        # 用户查询
        if any(keyword in input_lower for keyword in ['查询', '查看', '检查']) and any(
            keyword in input_lower for keyword in ['用户', 'user', '账号']
        ):
            username = self._extract_username(user_input)
            if username:
                return IntentType.USER_QUERY, {'user': username}, f"查询用户信息: {username}"

        # 目录位置/内容查询
        if any(keyword in input_lower for keyword in ['查询', '查看', '列出', '显示', '浏览', '搜索', '查找']):
            if any(keyword in input_lower for keyword in ['文件夹', '目录', 'folder', 'directory']):
                search_specific = any(
                    keyword in input_lower for keyword in ['.log', '日志', '后缀', '结尾']
                ) or ('所有' in input_lower and '文件' in input_lower)
                is_directory_lookup = any(
                    keyword in input_lower for keyword in ['位置', '在哪里', '在哪', 'ls']
                ) or not search_specific
                if is_directory_lookup:
                    path = self._extract_directory_path(user_input)
                    if path:
                        return IntentType.DIRECTORY_QUERY, {'path': path}, f"查看目录: {path}"

        # 文件搜索
        if any(keyword in input_lower for keyword in ['查找', '搜索', '检索', '寻找', 'find', '.log', '日志文件']):
            if any(keyword in input_lower for keyword in ['文件', '目录', '文件夹', '日志', '.log', '后缀', '结尾']):
                path = self._extract_search_path(user_input)
                pattern = self._extract_search_pattern(user_input)
                params = {'path': path}
                if pattern:
                    params['pattern'] = pattern
                explanation = f"搜索 {path} 下的文件"
                if pattern:
                    explanation += f"（模式: {pattern}）"
                return IntentType.FILE_SEARCH, params, explanation

        # 用户创建
        if any(keyword in input_lower for keyword in ['新增', '创建', '添加', 'new', 'create']):
            if any(keyword in input_lower for keyword in ['用户', 'user', '账号']):
                username = self._extract_username(user_input)
                # 尝试提取密码
                password = self._extract_password(user_input)
                params = {'user': username}
                if password:
                    params['password'] = password
                    return IntentType.USER_CREATE, params, f"创建用户: {username}（带密码）"
                else:
                    return IntentType.USER_CREATE, params, f"创建用户: {username}"

        # 目录创建
        if any(keyword in input_lower for keyword in ['新增', '创建', '新建', '添加', 'mkdir', 'create']):
            if any(keyword in input_lower for keyword in ['文件夹', '目录', 'folder', 'directory']):
                path = self._extract_directory_path(user_input)
                if path:
                    return IntentType.DIRECTORY_CREATE, {'path': path}, f"创建目录: {path}"

        # 用户删除
        elif any(keyword in input_lower for keyword in ['删除', 'del', 'remove', '删']):
            if any(keyword in input_lower for keyword in ['用户', 'user']):
                username = self._extract_username(user_input)
                if username:
                    return IntentType.USER_DELETE, {'user': username}, f"删除用户: {username}"
            if any(keyword in input_lower for keyword in ['文件夹', '目录', 'folder', 'directory']):
                path = self._extract_directory_path(user_input)
                if path:
                    return IntentType.FILE_DELETE, {'path': path, 'recursive': True}, f"删除目录: {path}"

        # 用户修改
        elif any(keyword in input_lower for keyword in ['修改', '更改', 'update', 'modify']):
            if any(keyword in input_lower for keyword in ['用户', 'user']):
                username = self._extract_username(user_input)
                if username:
                    return IntentType.USER_MODIFY, {'user': username}, f"修改用户: {username}"

        # 文件创建
        elif any(keyword in input_lower for keyword in ['创建', '新建', 'create']):
            if any(keyword in input_lower for keyword in ['文件夹', '目录', 'file', 'dir']):
                path = self._extract_path(user_input)
                return IntentType.FILE_CREATE, {'path': path}, f"创建文件夹: {path}"

        # 进程查询
        elif any(keyword in input_lower for keyword in ['进程', 'process']):
            return IntentType.PROCESS_LIST, {}, "列出进程"

        # 系统信息
        elif any(keyword in input_lower for keyword in ['系统', 'system', '信息']):
            return IntentType.SYSTEM_INFO, {}, "查询系统信息"

        return IntentType.UNKNOWN, {}, "无法识别的指令"

    def _extract_username(self, text: str) -> str:
        """从文本中提取用户名"""
        # 匹配各种格式："用户a"、"新增用户a"、"创建用户abc"等
        patterns = [
            r'查询[用户\s]*(\w+?)(?:是否存在|存在吗|信息)?$',
            r'查看[用户\s]*(\w+?)(?:是否存在|存在吗|信息)?$',
            r'用户[：:\s]*(\w+)',
            r'新增[用户\s]*(\w+)',
            r'创建[用户\s]*(\w+)',
            r'添加[用户\s]*(\w+)',
            r'user\s*[:：\s]*(\w+)',
            r'(\w+)\s*用户'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''

    def _extract_search_path(self, text: str) -> str:
        """从文本中提取搜索路径"""
        if any(keyword in text for keyword in ['当前文件夹', '当前目录', '当前路径']):
            return '.'

        if any(keyword in text for keyword in ['系统中', '全系统', '整个系统', '根目录']):
            return '/'

        match = re.search(r'(/[^ \n\t，。；、]+)', text)
        if match:
            return match.group(1)

        return '/'

    def _extract_search_pattern(self, text: str) -> str:
        """从文本中提取搜索模式"""
        text_lower = text.lower()

        wildcard_match = re.search(r'(\*\.[a-z0-9]+)', text_lower)
        if wildcard_match:
            return wildcard_match.group(1)

        ext_match = re.search(r'以\s*(\.[a-z0-9]+)\s*结尾', text_lower)
        if ext_match:
            return f"*{ext_match.group(1)}"

        inline_ext_match = re.search(r'(\.[a-z0-9]+)', text_lower)
        if inline_ext_match:
            return f"*{inline_ext_match.group(1)}"

        if '日志文件' in text:
            return '*.log'

        return ''

    def _extract_path(self, text: str) -> str:
        """从文本中提取路径"""
        # 匹配路径
        if '文件夹' in text:
            match = re.search(r'文件夹[：:\s]*(.+)', text)
            if match:
                return match.group(1)
        return './'

    def _extract_directory_path(self, text: str) -> str:
        """从文本中提取目录路径或目录名"""
        patterns = [
            r'(?:文件夹|目录)[：:\s]*(.+)',
            r'(?:新增|创建|新建|添加|删除|移除|删掉|查询|查看|列出|显示|浏览)(?:文件夹|目录)[：:\s]*(.+)',
            r'(?:mkdir)\s+(.+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                path = match.group(1).strip()
                path = re.sub(r'(?:的?位置|在哪里|在哪|是否存在)$', '', path).strip()
                if path:
                    return path
        return ''

    def _extract_password(self, text: str) -> str:
        """从文本中提取密码"""
        # 匹配密码
        patterns = [
            r'密码[：:\s]*(\w+)',
            r'密码是[：:\s]*(\w+)',
            r'passwd[：:\s]*(\w+)',
            r'pwd[：:\s]*(\w+)',
            r':(\w+)$'  # 匹配结尾的密码
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''

    def _determine_risk_level(self, intent: IntentType) -> RiskLevel:
        """根据意图确定风险等级"""
        if intent in [IntentType.FILE_DELETE, IntentType.USER_DELETE, IntentType.PROCESS_KILL]:
            return RiskLevel.HIGH
        elif intent in [IntentType.USER_CREATE, IntentType.FILE_CREATE, IntentType.USER_MODIFY]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def parse(self, user_input: str) -> Intent:
        """解析用户输入"""
        try:
            # 首先尝试简单的关键词匹配
            intent, params, explanation = self._simple_parse(user_input)
            if intent != IntentType.UNKNOWN:
                return Intent(
                    intent=intent,
                    risk_level=self._determine_risk_level(intent),
                    parameters=params,
                    explanation=explanation,
                    confidence=0.8
                )

            # 如果简单匹配失败，再尝试AI解析
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=30  # 添加30秒超时
            )

            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)

            # 解析意图类型
            intent_type_str = result_data.get('intent', 'unknown')
            intent_type = IntentType(intent_type_str)

            # 解析风险等级
            risk_level_str = result_data.get('risk_level', 'low')
            risk_level = RiskLevel(risk_level_str)

            return Intent(
                intent=intent_type,
                risk_level=risk_level,
                parameters=result_data.get('parameters', {}),
                explanation=result_data.get('explanation', ''),
                confidence=result_data.get('confidence', 0.0)
            )

        except APIError as e:
            # API错误时返回简单解析结果
            intent, params, explanation = self._simple_parse(user_input)
            return Intent(
                intent=intent,
                risk_level=self._determine_risk_level(intent),
                parameters=params,
                explanation=f"API解析失败，使用简单解析: {explanation}",
                confidence=0.5 if intent != IntentType.UNKNOWN else 0.0
            )
        except Exception as e:
            # 其他错误时返回未知意图
            return Intent(
                intent=IntentType.UNKNOWN,
                risk_level=RiskLevel.LOW,
                parameters={},
                explanation=f"意图识别失败: {str(e)}",
                confidence=0.0
            )

    def validate_parameters(self, intent: Intent) -> tuple[bool, str]:
        """验证参数是否完整"""
        required_params = {
            IntentType.FILE_SEARCH: ['path'],
            IntentType.FILE_DELETE: ['path'],
            IntentType.FILE_CREATE: ['path'],
            IntentType.DIRECTORY_CREATE: ['path'],
            IntentType.DIRECTORY_QUERY: ['path'],
            IntentType.USER_QUERY: ['user'],
            IntentType.PROCESS_QUERY: ['process'],
            IntentType.PROCESS_KILL: ['process'],
            IntentType.USER_CREATE: ['user'],
            IntentType.USER_DELETE: ['user'],
            IntentType.USER_MODIFY: ['user'],
            IntentType.PORT_QUERY: ['port'],
        }

        if intent.intent in required_params:
            for param in required_params[intent.intent]:
                if param not in intent.parameters or not intent.parameters[param]:
                    return False, f"缺少必需参数: {param}"

        return True, ""

    def enhance_with_context(self, intent: Intent, context: Dict[str, Any]) -> Intent:
        """使用上下文增强意图参数"""
        # 如果用户没有指定路径，尝试从上下文中获取
        if 'path' not in intent.parameters or not intent.parameters['path']:
            if 'last_path' in context:
                intent.parameters['path'] = context['last_path']

        # 如果没有指定用户，使用上下文中的用户
        if 'user' not in intent.parameters or not intent.parameters['user']:
            if 'last_user' in context:
                intent.parameters['user'] = context['last_user']

        return intent
