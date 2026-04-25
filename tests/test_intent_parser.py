import sys
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


class DummyOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._unexpected_create)
        )

    @staticmethod
    def _unexpected_create(*args, **kwargs):
        raise AssertionError("simple_parse should handle this input before API call")


class DummyBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


sys.modules["openai"] = types.SimpleNamespace(OpenAI=DummyOpenAI, APIError=Exception)
sys.modules["pydantic"] = types.SimpleNamespace(BaseModel=DummyBaseModel)
for module_name in ["intent", "intent.parser", "intent.schemas"]:
    sys.modules.pop(module_name, None)

from intent import IntentParser, IntentType


class IntentParserFileSearchTest(unittest.TestCase):
    def setUp(self):
        self.parser = IntentParser(
            base_url="https://example.com/v1",
            model="test-model",
            api_key="test-key"
        )

    def test_parse_system_wide_log_file_search(self):
        intent = self.parser.parse("查找系统中所有以 .log 结尾的日志文件")

        self.assertEqual(IntentType.FILE_SEARCH, intent.intent)
        self.assertEqual("/", intent.parameters["path"])
        self.assertEqual("*.log", intent.parameters["pattern"])

    def test_parse_current_directory_log_file_search(self):
        intent = self.parser.parse("查询当前文件夹下所有.log文件")

        self.assertEqual(IntentType.FILE_SEARCH, intent.intent)
        self.assertEqual(".", intent.parameters["path"])
        self.assertEqual("*.log", intent.parameters["pattern"])

    def test_parse_create_directory(self):
        intent = self.parser.parse("新增文件夹a")

        self.assertEqual(IntentType.DIRECTORY_CREATE, intent.intent)
        self.assertEqual("a", intent.parameters["path"])

    def test_parse_delete_directory(self):
        intent = self.parser.parse("删除文件夹a")

        self.assertEqual(IntentType.FILE_DELETE, intent.intent)
        self.assertEqual("a", intent.parameters["path"])
        self.assertTrue(intent.parameters["recursive"])

    def test_parse_query_directory(self):
        intent = self.parser.parse("查询文件夹a")

        self.assertEqual(IntentType.DIRECTORY_QUERY, intent.intent)
        self.assertEqual("a", intent.parameters["path"])

    def test_parse_query_directory_location(self):
        intent = self.parser.parse("查询文件夹a的位置")

        self.assertEqual(IntentType.DIRECTORY_QUERY, intent.intent)
        self.assertEqual("a", intent.parameters["path"])

    def test_parse_search_directory_location(self):
        intent = self.parser.parse("搜索文件夹b的位置")

        self.assertEqual(IntentType.DIRECTORY_QUERY, intent.intent)
        self.assertEqual("b", intent.parameters["path"])

    def test_parse_disk_usage_query(self):
        intent = self.parser.parse("查询磁盘的使用情况")

        self.assertEqual(IntentType.DISK_QUERY, intent.intent)

    def test_parse_current_disk_query(self):
        intent = self.parser.parse("查询当前磁盘")

        self.assertEqual(IntentType.DISK_QUERY, intent.intent)

    def test_parse_user_query(self):
        intent = self.parser.parse("查询用户a是否存在")

        self.assertEqual(IntentType.USER_QUERY, intent.intent)
        self.assertEqual("a", intent.parameters["user"])


if __name__ == "__main__":
    unittest.main()
