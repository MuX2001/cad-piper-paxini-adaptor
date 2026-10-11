"""Reference assembly in the Piper gripper-base frame (internal unit: mm)."""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import trimesh
from build123d import Pos, Rot, export_stl, import_step
from trimesh.transformations import euler_matrix

from parameters import M2324Reference


def jaw_transform(side: int, opening_mm: float) -> np.ndarray:
    """URDF jaw transform for side 1 or 2 at total gripper opening."""
    if side not in (1, 2) or not 0 <= opening_mm <= 100:
        raise ValueError("side must be 1 or 2 and opening must be 0..100 mm")
    yaw = 0 if side == 1 else -np.pi
    transform = euler_matrix(np.pi / 2, 0, yaw)
    transform[:3, 3] = (0, -opening_mm / 2 if side == 1 else opening_mm / 2, 138)
    return transform


def assembly_meshes(project: Path, opening_mm: float = 50) -> dict[str, trimesh.Trimesh]:
    """Return posed meshes, including unchanged vendor references."""
    source = project / "assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes"
    exported = project / "cad/exported"
    meshes = {}
    colors = {
        "gripper_base": (147, 153, 163, 255),
        "finger_1": (189, 195, 204, 255),
        "finger_2": (189, 195, 204, 255),
        "inner_plate": (55, 119, 200, 255),
        "outer_roof": (238, 148, 62, 255),
        "m2324_reference": (48, 167, 132, 255),
    }

    for name, filename, side in (
        ("gripper_base", "gripper_base.stl", None),
        ("finger_1", "gripper_link1.stl", 1),
        ("finger_2", "gripper_link2.stl", 2),
    ):
        mesh = trimesh.load_mesh(source / filename, process=True)
        mesh.apply_scale(1000)  # vendor STL coordinates are metres
        if side is not None:
            mesh.apply_transform(jaw_transform(side, opening_mm))
        mesh.visual.face_colors = colors[name]
        meshes[name] = mesh

    for side in (1, 2):
        jaw = jaw_transform(side, opening_mm)
        for name in ("inner_plate", "outer_roof"):
            mesh = trimesh.load_mesh(
                exported / f"piper_m2324-reference_{name}.stl", process=True
            )
            mesh.apply_transform(jaw)
            mesh.visual.face_colors = colors[name]
            meshes[f"{name}_{side}"] = mesh

    sensor_file = next(
        (project / "assets/vendor_files/GEN3触觉传感器3D模型").rglob("*M2324*.stp")
    )
    profile = M2324Reference()
    sensor = (
        Pos(0, profile.sensor_y_translation, profile.sensor_z_translation)
        * Rot(180, 0, 0)
        * import_step(sensor_file)
    )
    with TemporaryDirectory() as temporary:
        mesh_path = Path(temporary) / "sensor-reference.stl"
        export_stl(sensor, mesh_path, tolerance=0.08)
        mesh = trimesh.load_mesh(mesh_path, process=True)
    for side in (1, 2):
        posed = mesh.copy()
        posed.apply_transform(jaw_transform(side, opening_mm))
        posed.visual.face_colors = colors["m2324_reference"]
        meshes[f"m2324_sensor_{side}"] = posed
    return meshes
