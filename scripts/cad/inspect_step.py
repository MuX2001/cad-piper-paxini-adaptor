"""Show STEP header and unit declarations without interpreting geometry."""

import argparse
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="STEP or STP file to inspect")
    args = parser.parse_args()

    if args.path.suffix.lower() not in {".step", ".stp"}:
        parser.error("the input must be a STEP or STP file")

    content = args.path.read_text(encoding="latin-1")
    if "ISO-10303-21;" not in content[:256]:
        parser.error("the file does not start with a STEP physical-file header")

    for entity in ("FILE_NAME", "FILE_SCHEMA"):
        match = re.search(rf"\b{entity}\s*\(.*?\)\s*;", content, re.I | re.S)
        print(f"{entity}: {match.group(0).strip() if match else 'not found'}")

    declarations = sorted(
        set(re.findall(r"\b(?:SI_UNIT|CONVERSION_BASED_UNIT)\s*\([^;]*?\)", content, re.I | re.S))
    )
    print("Unit declarations (verify in CAD software):")
    for declaration in declarations:
        print(f"  {declaration.strip()}")
    if not declarations:
        print("  none found")


if __name__ == "__main__":
    main()
