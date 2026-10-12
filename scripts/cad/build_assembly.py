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
from parameters import PROFILES, clamp_profile  # noqa: E402


def render_view(meshes, path: Path, direction, caption: str,
                footer="Grey: stock gripper   Blue/orange: clamp   Green: supplied M2324 reference") -> None:
    """Draw a simple shaded orthographic review image from triangle meshes."""
    width, height = 1200, 900
    view = np.asarray(direction, dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross((0, 1, 0) if abs(view[2]) > 0.99 else (0, 0, 1), view)
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
            if float(normals[i] @ view) > 0:
                triangles.append((depth[face], xy[face], fill))

    pixels = np.full((height, width, 3), (248, 249, 250), dtype=np.uint8)
    zbuffer = np.full((height, width), -np.inf)
    for depths, triangle, fill in triangles:
        xmin, ymin = np.maximum(np.floor(triangle.min(axis=0)).astype(int), 0)
        xmax, ymax = np.minimum(np.ceil(triangle.max(axis=0)).astype(int), (width - 1, height - 1))
        if xmax < xmin or ymax < ymin:
            continue
        a, b, c = triangle
        denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(denominator) < 1e-10:
            continue
        xx, yy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        wa = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / denominator
        wb = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / denominator
        wc = 1 - wa - wb
        depth = wa * depths[0] + wb * depths[1] + wc * depths[2]
        patch = zbuffer[ymin:ymax + 1, xmin:xmax + 1]
        visible = (wa >= -1e-8) & (wb >= -1e-8) & (wc >= -1e-8) & (depth > patch)
        patch[visible] = depth[visible]
        pixels[ymin:ymax + 1, xmin:xmax + 1][visible] = fill
    image = Image.fromarray(pixels)
    draw = ImageDraw.Draw(image)
    draw.text((24, 20), caption, fill=(24, 30, 40))
    draw.text(
        (24, height - 32),
        footer,
        fill=(45, 53, 65),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opening-mm", type=float, default=50)
    parser.add_argument("--profile", choices=PROFILES, default="m2324-reference")
    args = parser.parse_args()
    meshes = assembly_meshes(PROJECT, args.opening_mm, args.profile)

    scene = trimesh.Scene()
    for name, mesh in meshes.items():
        glb_mesh = mesh.copy()
        glb_mesh.apply_scale(0.001)  # glTF defines metres
        scene.add_geometry(glb_mesh, geom_name=name, node_name=name)
    opening_label = f"{args.opening_mm:g}".replace(".", "p")
    label = "m2324" if args.profile == "m2324-reference" else args.profile
    glb = PROJECT / f"cad/exported/piper_dual_{label}_assembly_open{opening_label}.glb"
    glb.write_bytes(scene.export(file_type="glb"))

    screenshots = PROJECT / "drawings/screenshots"
    overview = {key: mesh for key, mesh in meshes.items() if key != "gripper_base"}
    render_view(
        overview, screenshots / f"piper_dual_{label}_assembly.png",
        (1.3, -1.8, 1.15), f"Piper dual M2324 assembly — {args.opening_mm:g} mm opening",
    )
    detail = {key: mesh for key, mesh in meshes.items() if key != "gripper_base"}
    render_view(
        detail, screenshots / f"piper_dual_{label}_mount_detail.png",
        (1.0, 0.0, 0.45), "Opposed M2324 mounting view",
    )
    print(glb)
    print(screenshots / f"piper_dual_{label}_assembly.png")
    print(screenshots / f"piper_dual_{label}_mount_detail.png")
    if args.profile == "m2324-v2":
        render_v2_details(screenshots)


def render_v2_details(destination):
    """Render exact CAD cuts, plus the actual distal-end-down roof orientation."""
    from tempfile import TemporaryDirectory
    from build123d import Box, Pos, export_stl
    from adapter import make_adapter

    clamp = clamp_profile("m2324-v2")
    inner, roof = make_adapter(clamp)
    with TemporaryDirectory() as temporary:
        def mesh_of(part, name, color):
            path = Path(temporary) / f"{name}.stl"
            export_stl(part, path)
            mesh = trimesh.load_mesh(path, process=True)
            mesh.visual.face_colors = color
            return mesh

        # Thin exact CAD slice exposes the cavity without the distal end wall
        # being projected behind it as though it filled the section.
        clip = Pos(0, -5.95, 0) * Box(150, 0.1, 150)
        sections = {
            "inner": mesh_of(inner & clip, "inner_section", (55, 119, 200, 255)),
            "roof": mesh_of(roof & clip, "roof_section", (238, 148, 62, 255)),
        }
        render_view(sections, destination / "piper_m2324-v2_section.png",
                    (0, -1, 0), "Y=-6 mm CAD section: unchanged cavity and distal bolt station",
                    "Blue: inner; orange: roof. Print roof with distal Y=2.1 face on bed; print-up is -Y.")
        x = clamp.cavity_half_width(-6) + clamp.bolt_offset_from_cavity
        detail_clip = Pos(x, -5.95, 9) * Box(10, 0.1, 14)
        bearing = mesh_of(roof & detail_clip, "bearing", (238, 148, 62, 255))
        render_view({"roof": bearing}, destination / "piper_m2324-v2_bearing.png",
                    (0, -1, 0), "Distal M3 seat: 0.5 mm recess; >=2.0 mm conservative roof allowance",
                    "Pocket cutter opens through sloped exterior. Actual seat-to-split support is checked separately.")
        mount = mesh_of(inner, "mount", (55, 119, 200, 255))
        render_view({"inner": mount}, destination / "piper_m2324-v2_mount_face.png",
                    (0, 0, -1), "Sensor rear mounting plane Z=-3.2 mm; six unchanged M1.6 axes",
                    "M2324 only. Window retained; no plug or cable envelope has been validated.")
        printing = mesh_of(roof, "printing", (238, 148, 62, 255))
        # New Z = distal_y - old Y, so the planar distal face lies on Z=0.
        transform = np.array([[1, 0, 0, 0], [0, 0, 1, 0],
                              [0, -1, 0, clamp.distal_y], [0, 0, 0, 1]], dtype=float)
        printing.apply_transform(transform)
        bed = trimesh.creation.box(extents=(60, 30, 0.4))
        bed.apply_translation((0, 12, -0.2))
        bed.visual.face_colors = (205, 211, 218, 255)
        render_view({"roof": printing, "bed": bed}, destination / "piper_m2324-v2_print_orientation.png",
                    (1.3, 1.8, 1.1), "Roof: distal end down, print-up = local -Y; external lug ramp <45 deg",
                    "Use brim. Inspect horizontal M3/head/tie holes for local supports; no 24-32 mm cavity bridge.")


if __name__ == "__main__":
    main()
