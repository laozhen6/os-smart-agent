import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

STDLIB_MODULES = {
    "abc",
    "argparse",
    "datetime",
    "enum",
    "json",
    "os",
    "pathlib",
    "random",
    "re",
    "string",
    "subprocess",
    "sys",
    "time",
    "typing",
}

LOCAL_MODULES = {
    "cli",
    "config",
    "conversation",
    "execution",
    "feedback",
    "intent",
    "security",
}

IMPORT_TO_REQUIREMENT = {
    "yaml": "pyyaml",
}


def top_level_requirement_name(raw_line: str) -> str:
    requirement = raw_line.split("#", 1)[0].strip()
    if not requirement:
        return ""

    for separator in ("<=", ">=", "==", "~=", "!=", "<", ">", "["):
        if separator in requirement:
            requirement = requirement.split(separator, 1)[0]
            break
    return requirement.strip().lower().replace("-", "_")


def imported_third_party_modules() -> set[str]:
    modules: set[str] = set()
    for py_file in SRC_DIR.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root not in STDLIB_MODULES and root not in LOCAL_MODULES:
                        modules.add(IMPORT_TO_REQUIREMENT.get(root, root))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    continue
                root = node.module.split(".", 1)[0]
                if root not in STDLIB_MODULES and root not in LOCAL_MODULES:
                    modules.add(IMPORT_TO_REQUIREMENT.get(root, root))
    return modules


class RequirementsCoverageTest(unittest.TestCase):
    def test_requirements_cover_runtime_imports(self):
        requirements = {
            top_level_requirement_name(line)
            for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
        }
        requirements.discard("")

        missing = sorted(imported_third_party_modules() - requirements)
        self.assertEqual(
            [],
            missing,
            msg=f"requirements.txt 缺少第三方依赖: {', '.join(missing)}",
        )


if __name__ == "__main__":
    unittest.main()
