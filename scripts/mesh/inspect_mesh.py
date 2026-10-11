"""Report basic STL geometry without changing the source file."""

import argparse
from pathlib import Path

import trimesh


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="STL file to inspect")
    parser.add_argument("--units", required=True, help="source length unit, e.g. mm or m")
    args = parser.parse_args()

    if args.path.suffix.lower() != ".stl":
        parser.error("the input must be an STL file")

    mesh = trimesh.load_mesh(args.path, file_type="stl", process=True)
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        parser.error("the STL contains no inspectable mesh")

    print(f"File: {args.path}")
    print(f"Vertices: {len(mesh.vertices)}; faces: {len(mesh.faces)}")
    print(f"Bounds ({args.units}): {mesh.bounds.tolist()}")
    print(f"Size ({args.units}): {mesh.extents.tolist()}")
    print(f"Watertight: {mesh.is_watertight}")
    if mesh.is_watertight:
        print(f"Volume ({args.units}^3): {abs(mesh.volume):.6g}")


if __name__ == "__main__":
    main()
