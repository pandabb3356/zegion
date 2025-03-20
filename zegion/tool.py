import ast
import json
from pathlib import Path

from agents import function_tool


@function_tool
def read_code_directory(code_dir: str) -> str:
    """
    Scans all Python files in the specified directory, parses the functions,
    classes, and their docstrings using the 'ast' module, and returns
    the extracted structure as a JSON string.

    Args:
        code_dir (str): The directory to scan for Python files.

    Returns:
        str: JSON formatted string with extracted functions and classes.
    """
    extracted_data = {}
    base_path = Path(code_dir)
    for file_path in base_path.rglob("*.py"):
        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            continue

        file_data = {"functions": [], "classes": []}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                }
                file_data["functions"].append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [],
                }
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        method_info = {
                            "name": sub_node.name,
                            "args": [arg.arg for arg in sub_node.args.args],
                            "docstring": ast.get_docstring(sub_node),
                        }
                        class_info["methods"].append(method_info)
                file_data["classes"].append(class_info)

        # Save the absolute path as string
        extracted_data[str(file_path).replace(f"{base_path}/", "")] = file_data

    return json.dumps(extracted_data, indent=2)


def extract_code_from_block(text: str) -> str:
    """
    Extracts the content from a code block enclosed in triple backticks.

    Parameters:
        text (str): A string containing a code block with triple backticks.

    Returns:
        str: The extracted code inside the code block, without the markers.
    """
    # Remove any extra whitespace around the text
    text = text.strip()

    # If the text starts with triple backticks, assume it's a code block
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove the first line if it starts with triple backticks (and possibly a language identifier)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove the last line if it is a standalone triple backticks
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        # Join the remaining lines and return the extracted code
        return "\n".join(lines).strip()

    # If no code block markers are found, return the original text
    return text
