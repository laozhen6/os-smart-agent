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
from execution.commands.user import UserCommands
from security import SecurityValidator


class RecordingExecutor(BaseExecutor):
    def __init__(self):
        super().__init__()
        self.commands = []

    def execute(self, command: str) -> ExecutionResult:
        self.commands.append(command)
        return ExecutionResult(True, "", "", 0)

    def execute_with_input(self, command: str, input_text: str) -> ExecutionResult:
        self.commands.append(command)
        return ExecutionResult(True, "", "", 0)

    def test_connection(self):
        return True, "ok"


class UserSecurityTest(unittest.TestCase):
    def test_create_user_rejects_dangerous_username_before_execution(self):
        executor = RecordingExecutor()
        commands = UserCommands(executor)

        result = commands.create_user("alice;rm -rf /", password="secret")

        self.assertFalse(result["success"])
        self.assertIn("危险", result["error"])
        self.assertEqual([], executor.commands)

    def test_delete_user_rejects_dangerous_username_before_execution(self):
        executor = RecordingExecutor()
        commands = UserCommands(executor)

        result = commands.delete_user("bob && userdel root")

        self.assertFalse(result["success"])
        self.assertIn("危险", result["error"])
        self.assertEqual([], executor.commands)

    def test_delete_user_allows_normal_username(self):
        executor = RecordingExecutor()
        commands = UserCommands(executor)

        result = commands.delete_user("alice")

        self.assertTrue(result["success"])
        self.assertIn("userdel alice", executor.commands)

    def test_security_validator_rejects_user_operation_command_injection(self):
        validator = SecurityValidator()

        is_safe, message = validator.validate_user_operation("eve$(rm -rf /)", "create")

        self.assertFalse(is_safe)
        self.assertIn("危险", message)

    def test_get_user_info_uses_id_command(self):
        executor = RecordingExecutor()
        commands = UserCommands(executor)

        result = commands.get_user_info("alice")

        self.assertTrue(result["success"])
        self.assertIn("id alice", executor.commands)


if __name__ == "__main__":
    unittest.main()
