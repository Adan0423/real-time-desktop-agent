from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    project_src = Path(__file__).resolve().parent / "src"
    sys.path.insert(0, str(project_src))

    from rtda.mcp.server import main as mcp_main

    return mcp_main(["--transport", "stdio"])


if __name__ == "__main__":
    raise SystemExit(main())
