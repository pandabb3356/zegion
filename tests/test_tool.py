import json
from pathlib import Path

import pytest

from zegion.tool import read_code_directory


class DummyContext:
    """Dummy context for tool invocation.

    This class serves as a placeholder to simulate the execution context during testing.
    """

    pass


@pytest.fixture
def code_directory(tmp_path: Path) -> Path:
    """Create a temporary directory with test Python files.

    This fixture creates a temporary directory containing:
      1. A valid Python file ("sample1.py") with correct syntax including a function and a class.
      2. An invalid Python file ("sample2.py") with syntax errors.

    Returns:
        Path: The path to the temporary directory containing the test files.
    """
    # Create a valid Python file with proper syntax.
    valid_file = tmp_path / "sample1.py"
    valid_file.write_text(
        '''
def foo(a, b):
    """This is foo"""
    return a + b

class Bar:
    """Bar class docstring"""
    def method1(self, x):
        """Method1 docstring"""
        return x
        ''',
        encoding="utf-8",
    )

    # Create an invalid Python file with syntax errors.
    invalid_file = tmp_path / "sample2.py"
    invalid_file.write_text(
        """
def bad_syntax(
    return None
        """,
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.asyncio
async def test_read_code_directory(code_directory: Path):
    """Test the read_code_directory tool using a temporary code directory.

    This test performs the following actions:
      - Initializes a dummy context for tool invocation.
      - Prepares tool input as a JSON string with the code directory path.
      - Calls the read_code_directory tool asynchronously.
      - Verifies that:
          * "sample1.py" is included in the result.
          * The function "foo" is detected in "sample1.py".
          * The class "Bar" is detected in "sample1.py".
          * The invalid file "sample2.py" is excluded from the results.

    Args:
        code_directory (Path): Temporary directory fixture containing test Python files.
    """
    # Initialize a dummy context to simulate the execution environment.
    ctx = DummyContext()

    # Prepare input parameters for the tool as a JSON string.
    input_data = json.dumps({"code_dir": str(code_directory)})

    # Invoke the read_code_directory tool asynchronously.
    result = await read_code_directory.on_invoke_tool(ctx, input_data)
    data = json.loads(result)

    # Verify that "sample1.py" is present in the parsed data.
    assert "sample1.py" in data
    sample1 = data["sample1.py"]

    # Verify that the function "foo" is detected in "sample1.py".
    functions = sample1.get("functions", [])
    assert any(func.get("name") == "foo" for func in functions)

    # Verify that the class "Bar" is detected in "sample1.py".
    classes = sample1.get("classes", [])
    assert any(cls.get("name") == "Bar" for cls in classes)

    # Verify that "sample2.py" (the file with syntax errors) is not included in the result.
    assert "sample2.py" not in data
