"""Test that all code examples in docs/usage.md actually work."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

DOCS_DIR = Path(__file__).parent.parent / "docs"
USAGE_MD = DOCS_DIR / "usage.md"


def _extract_python_blocks(markdown_text: str) -> Iterator[tuple[int, str]]:
    """Extract all Python code blocks from markdown text."""

    pattern = r"```python\n(.*?)\n```"
    for match in re.finditer(pattern, markdown_text, re.DOTALL):
        # Line number is count of newlines before the match, plus 2 (for ```python\n)
        line_num = markdown_text[: match.start()].count("\n") + 2
        yield line_num, match.group(1)


@pytest.mark.parametrize(
    ("line_num", "code"),
    list(_extract_python_blocks(USAGE_MD.read_text())),
    ids=lambda x: f"line_{x}" if isinstance(x, int) else "",
)
def test_code_block_executes(line_num: int, code: str) -> None:
    """Test that each code block in usage.md executes without error."""
    # Create a namespace with common imports
    import numpy as np

    namespace = {"__name__": "__main__", "__file__": str(USAGE_MD), "np": np}
    exec(code, namespace)  # noqa: S102
