"""Build the preliminary M2324-reference Piper adapter STEP and STL parts."""

import argparse
import sys
from pathlib import Path

from build123d import export_step, export_stl

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from adapter import make_adapter  # noqa: E402
from parameters import PROFILES, clamp_profile  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        required=True,
        choices=PROFILES,
        help="use the supplied M2324 interface; print two copies of each part",
    )
    args = parser.parse_args()
    inner_plate, outer_roof = make_adapter(clamp_profile(args.profile))
    destination = PROJECT / "cad" / "exported"
    destination.mkdir(exist_ok=True)

    for name, part in (("inner_plate", inner_plate), ("outer_roof", outer_roof)):
        prefix = destination / f"piper_{args.profile}_{name}"
        export_step(part, prefix.with_suffix(".step"))
        export_stl(part, prefix.with_suffix(".stl"))
        print(f"{name}: volume={part.volume:.2f} mm^3; {prefix}.step/.stl")


if __name__ == "__main__":
    main()
