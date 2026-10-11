"""Validate the preliminary M2324-reference clamp against supplied geometry."""

import sys
from pathlib import Path

import numpy as np
import trimesh
from build123d import Pos, Rot, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from adapter import make_adapter  # noqa: E402
from assembly import assembly_meshes, jaw_transform  # noqa: E402
from parameters import ClampParameters, M2324Reference  # noqa: E402


def intersecting_volume(a, b) -> float:
    common = a & b
    return 0 if common is None else common.volume


def finger_clearance(clamp: ClampParameters) -> tuple[float, float, float]:
    finger = trimesh.load_mesh(
        PROJECT / "assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/gripper_link1.stl",
        process=True,
    )
    vertices = finger.vertices * 1000
    vertices = vertices[
        (vertices[:, 1] >= clamp.proximal_y)
        & (vertices[:, 1] <= clamp.cavity_distal_y)
    ]
    # Include intersections with both axial ends so no spanning triangle is missed.
    for y in (clamp.proximal_y, clamp.cavity_distal_y):
        segments = trimesh.intersections.mesh_plane(
            finger, plane_normal=(0, 1, 0), plane_origin=(0, y / 1000, 0)
        )
        if len(segments):
            vertices = np.vstack((vertices, segments.reshape(-1, 3) * 1000))

    side = min(clamp.cavity_half_width(y) - abs(x) for x, y, z in vertices)
    roof = min(clamp.cavity_top(y) - z for x, y, z in vertices)
    plate = min(z - clamp.cavity_bottom for x, y, z in vertices)
    return side, roof, plate


def main() -> None:
    clamp = ClampParameters()
    profile = M2324Reference()
    inner, outer = make_adapter(clamp, profile)
    for name, part in (("inner_plate", inner), ("outer_roof", outer)):
        assert part.is_valid and len(part.solids()) == 1, f"{name}: invalid CAD solid"
        step_path = PROJECT / f"cad/exported/piper_m2324-reference_{name}.step"
        restored = import_step(step_path)
        assert restored.is_valid and len(restored.solids()) == 1
        assert abs(restored.volume - part.volume) < 0.01
        path = PROJECT / f"cad/exported/piper_m2324-reference_{name}.stl"
        mesh = trimesh.load_mesh(path, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
        relative_volume_error = abs(mesh.volume - part.volume) / part.volume
        assert relative_volume_error < 0.01, f"{name}: STL and CAD volumes differ"
        print(f"{name}: valid STEP solid, watertight STL, {part.volume:.2f} mm^3")

    margins = finger_clearance(clamp)
    assert min(margins) >= 0.5, f"finger-cavity reference clearance below 0.5 mm: {margins}"
    print("finger reference clearance, side/roof/plate (mm):", *(round(x, 3) for x in margins))

    sensor_path = next(
        (PROJECT / "assets/vendor_files/GEN3触觉传感器3D模型").rglob("*M2324*.stp")
    )
    sensor_native = import_step(sensor_path)
    hole_axes = set()
    for face in sensor_native.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() == GeomAbs_Cylinder and abs(surface.Cylinder().Radius() - 0.625) < 0.001:
            location = surface.Cylinder().Axis().Location()
            hole_axes.add((round(location.X(), 2), round(location.Y(), 2)))
    expected_axes = {(x, y) for x in profile.hole_x for y in profile.hole_y_native}
    assert hole_axes == expected_axes, f"unexpected STEP mounting axes: {hole_axes}"
    print("sensor STEP: six verified mounting axes at X=±8.75, Y=3/11/19 mm")

    sensor = (
        Pos(0, profile.sensor_y_translation, profile.sensor_z_translation)
        * Rot(180, 0, 0)
        * sensor_native
    )
    for name, volume in (
        ("sensor vs inner plate", intersecting_volume(sensor, inner)),
        ("sensor vs outer roof", intersecting_volume(sensor, outer)),
        ("two clamp halves", intersecting_volume(inner, outer)),
    ):
        assert volume < 0.001, f"{name}: {volume:.3f} mm^3 overlap"
        print(f"{name}: {volume:.6f} mm^3 overlap")

    roof_to_nut_wall = min(
        clamp.bolt_offset_from_cavity - clamp.nut_circumradius,
        clamp.side_wall - clamp.bolt_offset_from_cavity - clamp.nut_circumradius,
    )
    plate_below_sensor_head = (
        clamp.cavity_bottom - clamp.plate_bottom - clamp.sensor_head_recess
    )
    tie_lug_wall = min(
        (clamp.tie_lug_height - clamp.tie_hole_diameter) / 2,
        (clamp.tie_lug_length - clamp.tie_hole_diameter) / 2,
    )
    assert roof_to_nut_wall >= 1.2 and plate_below_sensor_head >= 1.2
    assert tie_lug_wall >= 1.2
    print(
        "nominal minimum webs, nut / sensor head / cable lug (mm):",
        round(roof_to_nut_wall, 2), round(plate_below_sensor_head, 2),
        round(tie_lug_wall, 2),
    )

    finger = trimesh.load_mesh(
        PROJECT / "assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/gripper_link1.stl",
        process=True,
    )
    finger.apply_scale(1000)
    inward_reach = max(
        -finger.bounds[0, 2], -inner.bounding_box().min.Z,
        -outer.bounding_box().min.Z, -sensor.bounding_box().min.Z,
    )
    print(f"each jaw assembly reaches into nominal closed gap: {inward_reach:.3f} mm")
    # The sensor's native active +Z becomes jaw-local -Z. The URDF rotations
    # map that normal into +Y on jaw 1 and -Y on jaw 2.
    active_normal = np.array((0.0, 0.0, -1.0))
    facing = [jaw_transform(side, 50)[:3, :3] @ active_normal for side in (1, 2)]
    assert np.allclose(facing[0], (0, 1, 0))
    assert np.allclose(facing[1], (0, -1, 0))
    print("active-face normals: jaw 1 +Y, jaw 2 -Y (opposed)")
    base = trimesh.load_mesh(
        PROJECT / "assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/gripper_base.stl",
        process=True,
    )
    base.apply_scale(1000)
    lowest_design_z = 138 + min(clamp.proximal_y, sensor.bounding_box().min.Y)
    print(f"clamp/sensor Z-envelope clearance above gripper base: {lowest_design_z - base.bounds[1, 2]:.3f} mm")
    assert lowest_design_z > base.bounds[1, 2]
    for opening in (0, 23, 24, 25, 50, 100):
        gap = opening - 2 * inward_reach
        print(f"opening {opening:3d} mm: paired-jaw Y-envelope gap {gap:.3f} mm")
        if opening >= 25:
            assert gap >= 2.0, "insufficient envelope clearance at operating opening"
    posed = assembly_meshes(PROJECT, 25)
    side_1 = [mesh for name, mesh in posed.items() if name.endswith("_1")]
    side_2 = [mesh for name, mesh in posed.items() if name.endswith("_2")]
    assert len(side_1) == len(side_2) == 4
    posed_gap = min(mesh.bounds[0, 1] for mesh in side_2) - max(
        mesh.bounds[1, 1] for mesh in side_1
    )
    assert posed_gap >= 2.0, f"posed paired-jaw gap {posed_gap:.3f} mm"
    print(f"posed STL assembly at 25 mm: {posed_gap:.3f} mm Y-envelope gap")
    print("Full closure is unsafe with both sensors installed; provisional command floor: 25 mm.")


if __name__ == "__main__":
    main()
