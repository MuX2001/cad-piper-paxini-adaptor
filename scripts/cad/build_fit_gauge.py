"""Export a short distal clamshell gauge before printing the full adapter."""

import sys
import argparse
from pathlib import Path

from build123d import Pos, Rot, export_step, export_stl

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from adapter import make_fit_gauge, make_fastener_coupon  # noqa: E402
from parameters import PROFILES, clamp_profile  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, default="m2324-reference")
    args = parser.parse_args()
    clamp = clamp_profile(args.profile)
    inner, roof = make_fit_gauge(clamp)
    prefix = "piper_finger" if args.profile == "m2324-reference" else f"piper_{args.profile}"
    for name, part in (("inner", inner), ("roof", roof)):
        path = PROJECT / f"cad/exported/{prefix}_fit_gauge_{name}.stl"
        export_stl(part, path)
        if args.profile == "m2324-v2":
            export_step(part, path.with_suffix(".step"))
            oriented = (Pos(0, 0, -clamp.plate_bottom) * part if name == "inner"
                        else Pos(0, 0, clamp.distal_y) * Rot(-90, 0, 0) * part)
            export_stl(oriented, path.with_stem(path.stem + "_print"))
        print(path)
    if args.profile == "m2324-v2":
        coupon = make_fastener_coupon(clamp)
        path = PROJECT / f"cad/exported/piper_{args.profile}_fastener_coupon.stl"
        export_stl(coupon, path)
        export_step(coupon, path.with_suffix(".step"))
        print(path)


if __name__ == "__main__":
    main()
