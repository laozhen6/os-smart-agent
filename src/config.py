import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config()
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _find_config(self) -> str:
        """查找配置文件"""
        possible_paths = [
            'config.yaml',
            'config.yml',
            os.path.join(os.path.dirname(__file__), '..', 'config.yaml'),
            os.path.expanduser('~/.os-smart-agent/config.yaml'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return 'config.yaml'

    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            'api': {
                'base_url': 'https://api.siliconflow.cn/v1',
                'model': 'deepseek-ai/DeepSeek-V3.2',
                'api_key': os.getenv('SILICONFLOW_API_KEY', ''),
            },
            'execution': {
                'mode': 'local',
                'timeout': 300,
            },
            'security': {
                'enable_secondary_confirmation': True,
                'max_command_timeout': 300,
                'risk_levels': {
                    'low': [],
                    'medium': [],
                    'high': [],
                },
            },
        }

    @property
    def api_base_url(self) -> str:
        return self._config.get('api', {}).get('base_url', 'https://api.siliconflow.cn/v1')

    @property
    def api_model(self) -> str:
        return self._config.get('api', {}).get('model', 'deepseek-ai/DeepSeek-V3.2')

    @property
    def api_key(self) -> str:
        return self._config.get('api', {}).get('api_key', os.getenv('SILICONFLOW_API_KEY', ''))

    @property
    def execution_mode(self) -> str:
        return self._config.get('execution', {}).get('mode', 'local')

    @property
    def execution_timeout(self) -> int:
        return self._config.get('execution', {}).get('timeout', 300)

    @property
    def ssh_config(self) -> Dict[str, Any]:
        return self._config.get('execution', {}).get('ssh', {})

    @property
    def enable_secondary_confirmation(self) -> bool:
        return self._config.get('security', {}).get('enable_secondary_confirmation', True)

    @property
    def max_command_timeout(self) -> int:
        return self._config.get('security', {}).get('max_command_timeout', 300)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def reload(self):
        """重新加载配置"""
        self._load_config()

    def get_system_type(self) -> str:
        """识别系统类型"""
        if os.path.exists('/etc/openEuler-release'):
            return 'openEuler'
        elif os.path.exists('/etc/centos-release'):
            return 'CentOS'
        elif os.path.exists('/etc/lsb-release') or os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                if 'ubuntu' in content.lower():
                    return 'Ubuntu'
        return 'Unknown'
