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


sys.modules.setdefault("paramiko", types.SimpleNamespace())
sys.modules.setdefault(
    "openai",
    types.SimpleNamespace(OpenAI=object, APIError=Exception),
)
sys.modules.setdefault("pydantic", types.SimpleNamespace(BaseModel=DummyBaseModel))

from execution.base import BaseExecutor, ExecutionResult
from execution.commands.file import FileCommands


class RecordingExecutor(BaseExecutor):
    def __init__(self, result: ExecutionResult):
        super().__init__()
        self.result = result
        self.commands = []

    def execute(self, command: str) -> ExecutionResult:
        self.commands.append(command)
        return self.result

    def execute_with_input(self, command: str, input_text: str) -> ExecutionResult:
        self.commands.append(command)
        return self.result

    def test_connection(self):
        return True, "ok"


class FileCommandsTest(unittest.TestCase):
    def test_search_files_accepts_find_exit_code_one(self):
        executor = RecordingExecutor(ExecutionResult(True, "/var/log/syslog\n", "", 0))
        commands = FileCommands(executor)

        result = commands.search_files("/", "*.log")

        self.assertTrue(result["success"])
        self.assertEqual(
            "find / -name '*.log' -type f 2>/dev/null; rc=$?; [ $rc -eq 0 ] || [ $rc -eq 1 ]",
            executor.commands[0]
        )

    def test_search_files_without_pattern_accepts_find_exit_code_one(self):
        executor = RecordingExecutor(ExecutionResult(True, "/tmp/demo.log\n", "", 0))
        commands = FileCommands(executor)

        result = commands.search_files("/")

        self.assertTrue(result["success"])
        self.assertEqual(
            "find / -type f 2>/dev/null | head -50; rc=$?; [ $rc -eq 0 ] || [ $rc -eq 1 ]",
            executor.commands[0]
        )

    def test_create_directory_uses_mkdir(self):
        executor = RecordingExecutor(ExecutionResult(True, "", "", 0))
        commands = FileCommands(executor)

        result = commands.create_directory("a")

        self.assertTrue(result["success"])
        self.assertEqual("mkdir -p a", executor.commands[0])

    def test_list_directory_outputs_location_and_listing(self):
        executor = RecordingExecutor(ExecutionResult(True, "", "", 0))
        commands = FileCommands(executor)

        result = commands.list_directory("a")

        self.assertTrue(result["success"])
        self.assertEqual("cd a 2>/dev/null && pwd && ls -lah .", executor.commands[0])


if __name__ == "__main__":
    unittest.main()
