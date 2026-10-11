"""Export an interactive assembly and orthographic PNG views."""

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from assembly import assembly_meshes  # noqa: E402


def render_view(meshes, path: Path, direction, caption: str) -> None:
    """Draw a simple shaded orthographic review image from triangle meshes."""
    width, height = 1200, 900
    view = np.asarray(direction, dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross((0, 0, 1), view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    target = np.array((0.0, 0.0, 95.0))
    points = np.vstack([mesh.vertices for mesh in meshes.values()])
    screen = np.column_stack(((points - target) @ right, (points - target) @ up))
    span = np.ptp(screen, axis=0)
    scale = min((width - 90) / span[0], (height - 110) / span[1])
    center = (screen.min(axis=0) + screen.max(axis=0)) / 2

    triangles = []
    light = np.array((0.35, -0.4, 0.85))
    light /= np.linalg.norm(light)
    for name, mesh in meshes.items():
        projected = np.column_stack(
            ((mesh.vertices - target) @ right, (mesh.vertices - target) @ up)
        )
        xy = (projected - center) * scale
        xy[:, 0] += width / 2
        xy[:, 1] = height / 2 - xy[:, 1]
        depth = (mesh.vertices - target) @ view
        faces = mesh.faces
        normals = mesh.face_normals
        color = np.array(mesh.visual.face_colors[0][:3], dtype=float)
        for i, face in enumerate(faces):
            shade = 0.63 + 0.37 * max(0.0, float(normals[i] @ light))
            fill = tuple(int(c) for c in np.clip(color * shade, 0, 255))
            triangles.append((float(depth[face].mean()), xy[face], fill))

    image = Image.new("RGB", (width, height), (248, 249, 250))
    draw = ImageDraw.Draw(image)
    for _, triangle, fill in sorted(triangles, key=lambda item: item[0]):
        draw.polygon([tuple(point) for point in triangle], fill=fill)
    draw.text((24, 20), caption, fill=(24, 30, 40))
    draw.text(
        (24, height - 32),
        "Grey: stock gripper   Blue/orange: printable clamp   Green: supplied M2324 reference",
        fill=(45, 53, 65),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opening-mm", type=float, default=50)
    args = parser.parse_args()
    meshes = assembly_meshes(PROJECT, args.opening_mm)

    scene = trimesh.Scene()
    for name, mesh in meshes.items():
        glb_mesh = mesh.copy()
        glb_mesh.apply_scale(0.001)  # glTF defines metres
        scene.add_geometry(glb_mesh, geom_name=name, node_name=name)
    opening_label = f"{args.opening_mm:g}".replace(".", "p")
    glb = PROJECT / f"cad/exported/piper_dual_m2324_assembly_open{opening_label}.glb"
    glb.write_bytes(scene.export(file_type="glb"))

    screenshots = PROJECT / "drawings/screenshots"
    overview = {key: mesh for key, mesh in meshes.items() if key != "gripper_base"}
    render_view(
        overview, screenshots / "piper_dual_m2324_assembly.png",
        (1.3, -1.8, 1.15), f"Piper dual M2324 assembly — {args.opening_mm:g} mm opening",
    )
    detail = {key: mesh for key, mesh in meshes.items() if key != "gripper_base"}
    render_view(
        detail, screenshots / "piper_dual_m2324_mount_detail.png",
        (1.0, 0.0, 0.45), "Opposed M2324 mounting view",
    )
    print(glb)
    print(screenshots / "piper_dual_m2324_assembly.png")
    print(screenshots / "piper_dual_m2324_mount_detail.png")


if __name__ == "__main__":
    main()
