import sys
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


class DummyBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


sys.modules.setdefault("pydantic", types.SimpleNamespace(BaseModel=DummyBaseModel))

from feedback.formatter import ResponseFormatter


class ResponseFormatterTest(unittest.TestCase):
    def test_format_directory_listing_includes_location(self):
        output = "/root/a\n" \
                 "total 0\n" \
                 "drwxr-xr-x 2 root root 4096 Apr 25 02:00 .\n"

        result = ResponseFormatter.format_directory_listing(output)

        self.assertIn("目录位置: /root/a", result)
        self.assertIn("目录内容:", result)
        self.assertIn("total 0", result)


if __name__ == "__main__":
    unittest.main()
