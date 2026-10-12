"""Validate the preliminary M2324-reference clamp against supplied geometry."""

import sys
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import trimesh
from build123d import Pos, Rot, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "cad" / "source"))

from adapter import make_adapter, make_fit_gauge, make_fastener_coupon  # noqa: E402
from assembly import assembly_meshes, jaw_transform  # noqa: E402
from parameters import ClampParameters, M2324Reference, PROFILES, clamp_profile  # noqa: E402


def intersecting_volume(a, b) -> float:
    common = a & b
    return 0 if common is None else common.volume


def finger_clearance(clamp: ClampParameters, side: int = 1) -> tuple[float, float, float]:
    finger = trimesh.load_mesh(
        PROJECT / f"assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/gripper_link{side}.stl",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, default="m2324-reference")
    parser.add_argument("--report", type=Path, help="JSON evidence path under workspace runs")
    args = parser.parse_args()
    clamp = clamp_profile(args.profile)
    profile = M2324Reference()
    inner, outer = make_adapter(clamp, profile)
    evidence = {"profile": args.profile, "units": "mm", "parameters": asdict(clamp),
                "sensor": asdict(profile), "parts": {}, "physical_validation": False}
    parts = {"inner_plate": inner, "outer_roof": outer}
    if args.profile == "m2324-v2":
        gauge_inner, gauge_roof = make_fit_gauge(clamp)
        parts.update(fit_gauge_inner=gauge_inner, fit_gauge_roof=gauge_roof,
                     fastener_coupon=make_fastener_coupon(clamp))
    for name, part in parts.items():
        assert part.is_valid and len(part.solids()) == 1, f"{name}: invalid CAD solid"
        step_path = PROJECT / f"cad/exported/piper_{args.profile}_{name}.step"
        restored = import_step(step_path)
        assert restored.is_valid and len(restored.solids()) == 1
        assert abs(restored.volume - part.volume) < 0.01
        path = PROJECT / f"cad/exported/piper_{args.profile}_{name}.stl"
        mesh = trimesh.load_mesh(path, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
        relative_volume_error = abs(mesh.volume - part.volume) / part.volume
        assert relative_volume_error < 0.01, f"{name}: STL and CAD volumes differ"
        print(f"{name}: valid STEP solid, watertight STL, {part.volume:.2f} mm^3")
        evidence["parts"][name] = {"cad_volume_mm3": part.volume,
            "step_valid_single_solid": True, "stl_watertight": True,
            "stl_winding_consistent": True, "stl_bodies": int(mesh.body_count),
            "stl_volume_relative_error": float(relative_volume_error),
            "step_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
            "stl_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    if args.profile == "m2324-reference":
        for name in ("inner", "roof"):
            mesh = trimesh.load_mesh(PROJECT / f"cad/exported/piper_finger_fit_gauge_{name}.stl", process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
        print("reference fit gauges: single-body, watertight, winding consistent")

    margins = finger_clearance(clamp)
    assert min(margins) >= 0.5, f"finger-cavity reference clearance below 0.5 mm: {margins}"
    print("finger reference clearance, side/roof/plate (mm):", *(round(x, 3) for x in margins))
    evidence["finger_clearance_mm"] = dict(zip(("side", "roof", "plate"), map(float, margins)))
    # Check both meshes independently: their coordinate roundoff differs.
    second_margins = finger_clearance(clamp, side=2)
    assert min(second_margins) >= 0.5
    evidence["finger_2_clearance_mm"] = dict(zip(("side", "roof", "plate"), map(float, second_margins)))
    evidence["finger_sections_mm"] = []
    for side in (1, 2):
        finger_mesh = trimesh.load_mesh(PROJECT / f"assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/gripper_link{side}.stl", process=True)
        for y in (-25, -15, -2):
            points = trimesh.intersections.mesh_plane(finger_mesh, (0, 1, 0), (0, y / 1000, 0)).reshape(-1, 3) * 1000
            low, high = points.min(axis=0), points.max(axis=0)
            evidence["finger_sections_mm"].append({"side": side, "y": y,
                "width": float(high[0] - low[0]), "thickness": float(high[2] - low[2]),
                "bottom_clearance": float(low[2] - clamp.cavity_bottom),
                "top_clearance": float(clamp.cavity_top(y) - high[2]),
                "total_vertical_clearance": float(clamp.cavity_top(y) - clamp.cavity_bottom - high[2] + low[2]),
                "total_lateral_clearance": float(2 * clamp.cavity_half_width(y) - high[0] + low[0])})

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
    evidence["overlap_mm3"] = {}
    for name, volume in (
        ("sensor vs inner plate", intersecting_volume(sensor, inner)),
        ("sensor vs outer roof", intersecting_volume(sensor, outer)),
        ("two clamp halves", intersecting_volume(inner, outer)),
    ):
        assert volume < 0.001, f"{name}: {volume:.3f} mm^3 overlap"
        print(f"{name}: {volume:.6f} mm^3 overlap")
        evidence["overlap_mm3"][name] = volume

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
    evidence["base_z_envelope_clearance_mm"] = float(lowest_design_z - base.bounds[1, 2])
    evidence["opening_gaps_mm"] = {}
    for opening in (0, 25, 30, 50, 100):
        gap = opening - 2 * inward_reach
        print(f"opening {opening:3d} mm: paired-jaw Y-envelope gap {gap:.3f} mm")
        evidence["opening_gaps_mm"][opening] = float(gap)
        if opening >= 30:
            assert gap >= 2.0, "insufficient envelope clearance at operating opening"
    posed = assembly_meshes(PROJECT, 30, args.profile)
    side_1 = [mesh for name, mesh in posed.items() if name.endswith("_1")]
    side_2 = [mesh for name, mesh in posed.items() if name.endswith("_2")]
    assert len(side_1) == len(side_2) == 4
    posed_gap = min(mesh.bounds[0, 1] for mesh in side_2) - max(
        mesh.bounds[1, 1] for mesh in side_1
    )
    assert posed_gap >= 7.0, f"posed paired-jaw gap {posed_gap:.3f} mm"
    print(f"posed STL assembly at 30 mm: {posed_gap:.3f} mm Y-envelope gap")
    evidence["posed_gap_at_30_mm"] = float(posed_gap)
    evidence["active_normals_world"] = [x.tolist() for x in facing]
    evidence["provisional_command_floor_mm"] = 30
    # Both moved assemblies remain above the base for every opening: jaw
    # motion changes only world Y, so this separating Z-plane is invariant.
    design_meshes = [m for name, m in posed.items() if name.startswith(("inner_plate", "outer_roof", "m2324_sensor"))]
    mesh_base_gap = min(m.bounds[0, 2] for m in design_meshes) - posed["gripper_base"].bounds[1, 2]
    assert mesh_base_gap > 0
    evidence["posed_base_clearance_mm"] = float(mesh_base_gap)
    print("Full closure is unsafe; conservative software trial floor: 30 mm (not a final limit).")

    if args.profile == "m2324-v2":
        validate_v2(clamp, inner, outer, parts, profile, evidence)
        glb_path = PROJECT / "cad/exported/piper_dual_m2324-v2_assembly_open50.glb"
        scene = trimesh.load(glb_path, force="scene")
        expected = assembly_meshes(PROJECT, 50, args.profile)
        assert set(scene.graph.nodes_geometry) == set(expected)
        assert len(scene.geometry) == 9
        for name, original in expected.items():
            transform, geometry = scene.graph[name]
            restored_mesh = scene.geometry[geometry].copy()
            restored_mesh.apply_transform(transform)
            assert np.allclose(restored_mesh.bounds * 1000, original.bounds, atol=1e-4, rtol=0)
        evidence["glb"] = {"nodes": 9, "opening_mm": 50, "units": "metres",
                           "posed_bounds_verified": True,
                           "sha256": hashlib.sha256(glb_path.read_bytes()).hexdigest()}
    evidence["input_sha256"] = {
        str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for folder in ("cad/source", "scripts/cad", "assets/vendor_files")
        for path in sorted((PROJECT / folder).rglob("*")) if path.is_file()
        and "__pycache__" not in path.parts
    }
    evidence["requirements_lock_sha256"] = hashlib.sha256((PROJECT / "requirements.lock").read_bytes()).hexdigest()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(evidence, indent=2) + "\n")
        print(args.report)


def validate_v2(clamp, inner, roof, parts, sensor, evidence):
    reference = ClampParameters()
    changed = {key for key, value in asdict(clamp).items() if value != asdict(reference)[key]}
    assert changed == {"bolt_head_recess", "open_head_pockets", "lug_print_ramp_run"}
    old_inner, old_roof = make_adapter(reference)
    assert abs(inner.volume - old_inner.volume) < 1e-6
    assert intersecting_volume(inner, old_inner) > inner.volume - 1e-6
    assert sensor == M2324Reference()
    rear_z = sensor.sensor_z_translation - sensor.back_plane_native_z
    assert abs(rear_z - clamp.plate_bottom) < 1e-9
    # OCCT bounding boxes include the shape tolerance (~1e-7 mm).
    assert abs(inner.bounding_box().min.Z - rear_z) < 1e-6
    # Verify the actual cylindrical through axes in the exported inner solid.
    mounting_axes = set()
    for face in inner.faces():
        surf = BRepAdaptor_Surface(face.wrapped)
        if surf.GetType() == GeomAbs_Cylinder and abs(surf.Cylinder().Radius() - 0.9) < 1e-6:
            loc = surf.Cylinder().Axis().Location()
            mounting_axes.add((round(loc.X(), 4), round(loc.Y(), 4)))
    assert mounting_axes == {(round(x, 4), round(y, 4)) for x, y in sensor.hole_positions_in_jaw}
    evidence["invariants"] = {"changed_parameters": sorted(changed), "inner_identical_to_reference": True,
        "sensor_mounting_axes_mm": sorted(mounting_axes), "rear_mounting_plane_z_mm": rear_z,
        "cavity_parameters_unchanged": True}
    # Directly test the reference cavity void, not only the parameter values.
    from adapter import _section, _cylinder
    from build123d import Solid
    cavity = Solid.make_loft([
        _section(reference.cavity_proximal_y, reference.cavity_half_width_proximal,
                 reference.cavity_bottom, reference.cavity_top_proximal),
        _section(reference.cavity_distal_y, reference.cavity_half_width_distal,
                 reference.cavity_bottom, reference.cavity_top_distal)], ruled=True)
    assert intersecting_volume(roof, cavity) < 1e-6
    assert intersecting_volume(inner, cavity) < 1e-6
    evidence["invariants"]["reference_cavity_intrusion_mm3"] = 0

    slope = abs((clamp.cavity_top_distal - clamp.cavity_top_proximal) /
                (clamp.cavity_distal_y - clamp.cavity_proximal_y))
    head_r = (clamp.bolt_head_diameter + clamp.head_diameter_compensation) / 2
    conservative_web = clamp.roof_wall - clamp.bolt_head_recess - slope * head_r
    assert conservative_web >= 2.0
    evidence["conservative_roof_allowance_mm"] = conservative_web
    evidence["bolt_stations"] = []
    for y in clamp.bolt_stations_y:
        seat_z = clamp.cavity_top(y) + clamp.roof_wall - clamp.bolt_head_recess
        for sign in (-1, 1):
            x = sign * (clamp.cavity_half_width(y) + clamp.bolt_offset_from_cavity)
            # Exact full annular volume test in addition to point samples.
            annulus = (_cylinder(x, y, seat_z - 1, head_r, 2)
                       - _cylinder(x, y, seat_z - 1, clamp.bolt_clearance_diameter / 2, 2.2))
            missing_support = annulus.volume - intersecting_volume(annulus, roof)
            assert abs(missing_support) < 1e-5
            # Sample the complete annular support down to 2 mm below the seat.
            for radius in (1.8, 2.4, 3.0):
                for theta in np.linspace(0, 2 * np.pi, 36, endpoint=False):
                    for depth in (0.01, 1.0, 2.0):
                        assert roof.is_inside((x + radius * np.cos(theta), y + radius * np.sin(theta), seat_z - depth))
            # The pocket mouth is open above the seat at every angular sample.
            for theta in np.linspace(0, 2 * np.pi, 36, endpoint=False):
                assert not roof.is_inside((x + 2.5 * np.cos(theta), y + 2.5 * np.sin(theta), seat_z + 0.05))
        nut_top_z = clamp.plate_bottom + clamp.nut_recess
        grip = seat_z - nut_top_z
        evidence["bolt_stations"].append({"y_mm": y, "seat_z_mm": seat_z,
            "seat_to_split_mm": seat_z - clamp.split_z, "seat_to_nut_top_mm": grip,
            "screw_reach_into_nut_mm": {str(length): length - grip for length in (14, 16, 18)}})
    print(f"V2 conservative roof allowance {conservative_web:.3f} mm; all four seats support >=2 mm sampled annulus")
    evidence["full_2mm_bearing_annuli_verified"] = True
    # Distal-end-down printing leaves the cavity open on each layer; the end
    # stop prints first. No datum is removed or displaced to form a ceiling.
    assert abs(parts["fit_gauge_roof"].bounding_box().min.Y + 10) < 1e-6
    assert abs(parts["fit_gauge_roof"].bounding_box().max.Y - clamp.distal_y) < 1e-6
    for name in ("fit_gauge_inner", "fit_gauge_roof"):
        assert parts[name].bounding_box().min.Y < -6 - clamp.nut_circumradius
        assert parts[name].bounding_box().max.Y > clamp.cavity_distal_y
        path = PROJECT / f"cad/exported/piper_m2324-v2_{name}_print.stl"
        mesh = trimesh.load_mesh(path, process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
        assert abs(mesh.bounds[0, 2]) < 1e-5
        assert abs(mesh.volume - parts[name].volume) / parts[name].volume < 0.01
        # Invert the print transform and compare the tessellated geometry.
        local = mesh.copy()
        if name == "fit_gauge_inner":
            local.apply_translation((0, 0, clamp.plate_bottom))
        else:
            local.apply_translation((0, 0, -clamp.distal_y))
            local.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
        raw = trimesh.load_mesh(PROJECT / f"cad/exported/piper_m2324-v2_{name}.stl", process=True)
        from scipy.spatial import cKDTree
        assert cKDTree(raw.vertices).query(local.vertices)[0].max() < 1e-4
        evidence["parts"][name]["print_stl_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        evidence["parts"][name]["print_stl_verified"] = True
    # Gauge is literally the full-part intersection; both distal M3 positions
    # and 1.5 mm distal stop are retained with positive pocket-edge margin.
    ramp_angle = np.degrees(np.arctan((clamp.tie_lug_height + 0.1) / clamp.lug_print_ramp_run + slope))
    assert ramp_angle <= 45
    evidence["printing"] = {"roof_bed_plane": "local Y=2.1", "roof_print_up": "local -Y",
        "cavity_bridge_in_recommended_orientation_mm": 0, "lug_ramp_angle_from_print_vertical_deg": float(ramp_angle),
        "local_support_review": "horizontal M3/head/tie bores; inner nut-pocket ceilings",
        "slicer_or_print_verified": False, "gauge_y_extent_mm": [-10, 2.1]}
    print("V2 unchanged sensor axes/rear plane, unchanged cavity parameters, full distal M3 gauge pair verified")


if __name__ == "__main__":
    main()
