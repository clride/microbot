import sys
import os
from pathlib import Path

import subprocess
import sys
import tempfile
import textwrap

import shlex
import re

from commands.command import Command

SANDBOX_ROOT = Path(os.getcwd()).resolve()
SANDBOX_ROOT = SANDBOX_ROOT / "ai_workspace"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)

class Help(Command):
    name = "help"
    description = "Lists all available commands."

    def execute(self) -> str:
        lines = [
            f"{name} - {cls.description}"
            for name, cls in Command.registry.items()
        ]
        return "\n".join(sorted(lines))

def resolve_sandbox_path(user_path: str) -> Path:
    """
    Resolve a user-provided path and ensure it stays inside the sandbox root.
    Raises PermissionError if attempting to escape.
    """
    target_path = (SANDBOX_ROOT / user_path).resolve()

    if not (target_path == SANDBOX_ROOT or SANDBOX_ROOT in target_path.parents):
        raise PermissionError("Access denied: Path escapes sandbox.")

    return target_path


class ReadFile(Command):
    name = "cat"
    description = "Reads the contents of a file inside the sandbox."

    def execute(self, file_path: str) -> str:
        path = resolve_sandbox_path(file_path)
        with open(path, 'r') as f:
            return f.read()

class WriteFile(Command):
    name = "createfile"
    description = "Writes a string to a file inside the sandbox."

    def execute(self, file_path: str, content: str) -> None:
        path = resolve_sandbox_path(file_path)

        print("Writing to:", path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("Write successful")

class AppendFile(Command):
    name = "appendfile"
    description = "Appends a string to a file inside the sandbox."

    def execute(self, file_path: str, content: str) -> None:
        path = resolve_sandbox_path(file_path)

        print("Appending to:", path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'a', encoding='utf-8') as f:
            f.write("\n"+content)

        print("Append successful")

class MakeDirectory(Command):
    name = "mkdir"
    description = "Creates a directory inside the sandbox."

    def execute(self, dir_path: str) -> None:
        path = resolve_sandbox_path(dir_path)
        path.mkdir(parents=True, exist_ok=True)


class ListDirectory(Command):
    name = "ls"
    description = "Lists contents of the current working directory."

    def execute(self) -> list:
        path = resolve_sandbox_path(".")
        return os.listdir(path)


class DeleteFile(Command):
    name = "rm"
    description = "Deletes a file inside the sandbox."

    def execute(self, file_path: str) -> None:
        path = resolve_sandbox_path(file_path)
        path.unlink()


class DeleteDirectory(Command):
    name = "rmdir"
    description = "Deletes a directory inside the sandbox."

    def execute(self, dir_path: str) -> None:
        path = resolve_sandbox_path(dir_path)
        import shutil
        shutil.rmtree(path)

class GetFileSize(Command):
    name = "size"
    description = "Returns the size of a file inside the sandbox."

    def execute(self, file_path: str) -> int:
        path = resolve_sandbox_path(file_path)
        return path.stat().st_size
    
class RunPython(Command):
    name = "python"
    description = "Executes a Python script inside the sandbox and returns its output."

    def execute(self, code: str):
        return self.run_restricted_python(code)

    def run_restricted_python(self, code: str):
        banned = ["import", "__", "open(", "exec(", "eval(", "os.", "sys.", "subprocess"]
        if any(b in code for b in banned):
            raise PermissionError("Restricted keyword detected. You may not use: " + ", ".join(banned))

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as f:
            f.write(textwrap.dedent(code))
            filename = f.name

        try:
            result = subprocess.run(
                [sys.executable, filename],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            raise TimeoutError("Execution timed out.")

def run_command(input_string: str):
    match = re.fullmatch(r"\[\[(.*?)\]\]", input_string.strip())
    if not match:
        return "Invalid format. Use [[/command args]]"

    command_text = match.group(1).strip()

    if not command_text.startswith("/"):
        return "Commands must start with /"

    try:
        parts = shlex.split(command_text[1:])
    except ValueError as e:
        return f"Parsing error: {str(e)}"

    if not parts:
        return "No command provided."

    command_name = parts[0]
    args = parts[1:]

    command_class = Command.registry.get(command_name)

    if not command_class:
        return f"Unknown command: {command_name}"

    try:
        command_instance = command_class()
        result = command_instance.execute(*args)
        return result if result is not None else "Command executed successfully with no output."
    except TypeError as e:
        return f"Invalid arguments for command '{command_name}'. Error: {str(e)}"
    except Exception as e:
        return f"Error executing command '{command_name}': {str(e)}"