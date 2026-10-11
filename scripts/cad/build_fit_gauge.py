"""Export a short distal clamshell gauge before printing the full adapter."""

import sys
from pathlib import Path

from build123d import Box, Pos, export_stl

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from adapter import make_adapter  # noqa: E402


def main() -> None:
    inner, roof = make_adapter()
    # Covers the distal bolt station and end stop, using the same cavity as the full part.
    gauge = Pos(0, -3.95, 0) * Box(150, 12.1, 100)
    for name, part in (("inner", inner & gauge), ("roof", roof & gauge)):
        path = PROJECT / f"cad/exported/piper_finger_fit_gauge_{name}.stl"
        export_stl(part, path)
        print(path)


if __name__ == "__main__":
    main()
