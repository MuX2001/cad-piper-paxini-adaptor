"""Regenerate only v2/: parts, complete mesh assemblies, STEP, previews, evidence."""

import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from dataclasses import asdict
from pathlib import Path
import sys

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / "cad/source"))

import numpy as np
import trimesh
from build123d import Color, Compound, Pos, export_step, export_stl

from references import (ROOT, GRIPPER, SENSOR, cad_mesh, carrier_and_finger, faceted_solid,
                        jaw_matrix, mating_holes, sensor_mounting_axes, vendor_mesh,
                        reach_measurements, connector_measurements)
from replacement_finger import (P, cable_envelope, hardware, jaw_location, make_coupon,
                                make_finger, make_flange, placed_sensor, plug_envelope, print_location,
                                service_cable, strain_relief_band, root_key_envelope)
from render import render

BLUE = (39, 123, 196, 255)
GREEN = (37, 169, 126, 255)
GREY = (141, 153, 168, 255)
STEEL = (191, 201, 213, 255)
AMBER = (238, 158, 41, 255)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_preservation():
    initial = json.loads((V2 / "docs/preserved-state.json").read_text())
    protected = {**initial["files"], **initial.get("subsequent_user_inputs", {})}
    changed = [name for name, digest in protected.items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
    extra = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()
             and not any(s.startswith(".") for s in p.relative_to(ROOT).parts)
             and p.relative_to(ROOT).parts[0] != "v2" and str(p.relative_to(ROOT)) not in protected]
    assert not changed, f"Protected pre-existing files changed: {changed}"
    assert not extra, f"New files outside isolated v2/: {extra}"
    previous = json.loads((V2 / "docs/previous-revision.json").read_text())
    revision_changed = [name for name,digest in previous["files"].items()
                        if sha(V2 / previous["snapshot"] / name) != digest]
    assert not revision_changed, f"Previous V2 snapshot changed: {revision_changed}"
    return {"pre_existing_files": len(initial["files"]), "changed": changed,
            "subsequent_user_inputs": len(initial.get("subsequent_user_inputs", {})),
            "new_files_outside_v2": extra, "initial_head": initial["head"],
            "previous_v2_commit":previous["git_commit"], "previous_v2_files":len(previous["files"]),
            "previous_v2_changed":revision_changed}


def local_meshes(finger, sensor):
    carrier = carrier_and_finger(1)[0]
    carrier.visual.face_colors = STEEL
    meshes = {"retained_carrier": carrier, "replacement_finger": cad_mesh(finger, BLUE),
              "M2324": cad_mesh(sensor, GREEN)}
    meshes.update({name: cad_mesh(shape, STEEL) for name, shape in hardware().items()})
    return meshes


def assembly_meshes(local, opening, with_cable=True):
    base = vendor_mesh("gripper_base")
    base.visual.face_colors = GREY
    meshes = {"original_actuator_and_transmission": base}
    for side in (1, 2):
        for name, mesh in local.items():
            # Import the second retained body independently, not a replacement proxy.
            if name == "retained_carrier":
                mesh = carrier_and_finger(side)[0]
                mesh.visual.face_colors = STEEL
            posed = mesh.copy()
            posed.apply_transform(jaw_matrix(side, opening))
            meshes[f"{name}_{side}"] = posed
        if with_cable:
            for name, shape in (("DF53_exposed_plug", plug_envelope()), ("moving_harness_envelope", cable_envelope()),
                                ("releasable_tie_envelope", strain_relief_band())):
                posed = cad_mesh(shape, AMBER)
                posed.apply_transform(jaw_matrix(side, opening))
                meshes[f"{name}_{side}"] = posed
            meshes[f"service_loop_envelope_{side}"] = cad_mesh(service_cable(side, opening), AMBER)
    return meshes


def export_scene(meshes, path):
    scene = trimesh.Scene()
    for name, mesh in meshes.items():
        mesh = mesh.copy()
        mesh.apply_scale(.001)  # GLB metres; STEP/STL mm.
        scene.add_geometry(mesh, geom_name=name, node_name=name)
    path.write_bytes(scene.export(file_type="glb"))


def export_print_mesh(part, path):
    """Discard only zero-area pole facets from authored CAD tessellation.

    No vertex movement, hole filling or vendor-mesh modification is permitted.
    Rounded B-rep surfaces can produce collapsed UV-pole triangles in STL.
    """
    export_stl(part, path, tolerance=.03, angular_tolerance=.15)
    mesh = trimesh.load_mesh(path, process=True)
    raw_count = len(mesh.faces)
    keep = mesh.nondegenerate_faces()
    removed_area = float(mesh.area_faces[~keep].max()) if (~keep).any() else 0.0
    assert removed_area <= 1e-12, f"Nonzero-area degenerate facets in {path.name}"
    mesh.update_faces(keep)
    unique = mesh.unique_faces()
    duplicate_count = int((~unique).sum())
    mesh.update_faces(unique)
    mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1, path.name
    assert mesh.volume > 0 and abs(mesh.volume / part.volume - 1) < .005, path.name
    if len(mesh.faces) != raw_count:
        path.write_bytes(mesh.export(file_type="stl"))
    return {"raw_facets":raw_count, "exported_facets":len(mesh.faces),
            "zero_area_facets_removed":int((~keep).sum()),
            "maximum_removed_facet_area_mm2":removed_area,
            "duplicate_facets_removed":duplicate_count,
            "vertices_moved":False, "holes_filled":False}


def reference_report():
    report = {"units": "mm", "method": "Read-only imports; STL metres multiplied by 1000; no mesh repairs",
              "carriers": {}, "sensor": {"axes_xy_native_mm": sensor_mounting_axes(),
              "source": str(SENSOR.relative_to(ROOT)), "sha256": sha(SENSOR)},
              "functional_reach": reach_measurements(), "parallel_connector_mouths": connector_measurements()}
    for side in (1, 2):
        carrier, finger = carrier_and_finger(side)
        circles = mating_holes(carrier)
        pilot = []
        for hole in circles:
            if abs(hole["x"]) < 1:
                continue
            vertices = carrier.vertices
            radii = np.hypot(vertices[:, 0] - hole["x"], vertices[:, 2] - hole["z"])
            ring = vertices[np.abs(radii - .8) < .001]
            assert len(ring) >= 24
            pilot.append({"x": hole["x"], "z": hole["z"], "radius_mm": .8,
                          "y_range_mm": [float(ring[:, 1].min()), float(ring[:, 1].max())]})
        source = GRIPPER / f"meshes/gripper_link{side}.stl"
        report["carriers"][str(side)] = {"source": str(source.relative_to(ROOT)), "sha256": sha(source),
            "retained_triangles": len(carrier.faces), "retained_watertight": bool(carrier.is_watertight),
            "retained_bounds_mm": carrier.bounds.tolist(), "mating_plane_boundary_circles": circles,
            "pilot_cylinders": pilot, "removed_reference_triangles": len(finger.faces),
            "thread": "M2 inferred from 1.6 mm pilot and 2.4 mm stock clearance; pitch NOT modeled/verified",
            "physical_removability": "Separate coincident mating bodies in CAD; verify real hardware before disassembly"}
    return report


def build():
    preservation = check_preservation()
    exports, drawings = V2 / "cad/exported", V2 / "drawings"
    exports.mkdir(parents=True, exist_ok=True)
    drawings.mkdir(parents=True, exist_ok=True)
    finger, sensor, flange, coupon = make_finger(), placed_sensor(), make_flange(), make_coupon()
    parts = {"replacement_finger": finger, "mount_fit_gauge": flange, "fastener_coupon": coupon}
    stl_audit = {}
    for name, part in parts.items():
        export_step(part, exports / f"{name}.step")
        stl_audit[f"{name}.stl"] = export_print_mesh(part, exports / f"{name}.stl")
        printable = print_location() * part if name == "replacement_finger" else part
        if name == "mount_fit_gauge":
            # Flange rear on bed: new Z = old Y - mount_y.
            from build123d import Rot
            printable = Pos(0, P.carrier_z_max, -P.mount_y) * Rot(90, 0, 0) * part
        stl_audit[f"{name}_print.stl"] = export_print_mesh(printable, exports / f"{name}_print.stl")
    local = local_meshes(finger, sensor)
    for opening in (0, 50, 100):
        meshes = assembly_meshes(local, opening)
        export_scene(meshes, exports / f"assembly_open{opening}.glb")
        direction = (1.3, -1.8, 1.0) if opening == 50 else (1, 0, .18)
        render(meshes, drawings / f"assembly_open{opening}.png", direction,
               f"PiPER / PaXini V2 — {opening} mm commanded opening",
               "Grey: original mechanism   Blue: replacement fingers   Green: M2324   Amber: provisional harness envelope")
    details = {k: m for k, m in assembly_meshes(local, 50, with_cable=False).items() if k != "original_actuator_and_transmission"}
    render(details, drawings / "opposed_sensors.png", (1, 0, .3),
           "Two identical fingers / opposed sensing faces",
           f"50 mm commanded opening; {50 + 2 * sensor.bounding_box().min.Z:.3f} mm conservative sensor-envelope gap")

    # STEP contains editable B-reps of the designed pair, sensors, and the actual
    # triangulated retained carriers. Original actuator is mesh-only in GLB.
    children = []
    for side in (1, 2):
        for name, shape, color in (("replacement_finger", finger, BLUE), ("M2324", sensor, GREEN),
                                   ("retained_carrier_faceted", faceted_solid(carrier_and_finger(side)[0]), STEEL)):
            # Separate B-rep identities preserve instance labels on STEP import.
            child = jaw_location(side, 50) * deepcopy(shape)
            child.label = f"{name}_{side}"
            child.color = Color(*(c / 255 for c in color[:3]))
            children.append(child)
    export_step(Compound(children=children, label="V2 pair; actuator mesh in assembly_open50.glb"),
                exports / "finger_sensor_pair_open50.step")

    cables = assembly_meshes(local, 50, with_cable=True)
    export_scene(cables, exports / "assembly_open50_cable_study.glb")
    cable_children = []
    for side in (1,2):
        for name, shape in (("DF53_exposed_plug", jaw_location(side,50)*plug_envelope()),
                            ("moving_harness_envelope", jaw_location(side,50)*cable_envelope()),
                            ("releasable_tie_envelope", jaw_location(side,50)*strain_relief_band()),
                            ("service_loop_envelope", service_cable(side,50))):
            shape = deepcopy(shape)
            shape.label = f"{name}_{side}"
            cable_children.append(shape)
    export_step(Compound(children=cable_children, label="Cable clearance study; harness dimensions provisional"),
                exports / "cable_routing_open50.step")
    cable_detail = {**local, "plug":cad_mesh(plug_envelope(),AMBER),
                    "parallel_leads":cad_mesh(cable_envelope(),AMBER), "tie":cad_mesh(strain_relief_band(),STEEL)}
    render(cable_detail, drawings / "cable_routing.png", (0,0,1),
           "Rear view / parallel connector exit / open strain-relief saddle",
           "Parallel plug exit visible here; leads and tie run on the opposite, grasp-facing side of the new skin.",
           labels=[((P.plug_center_x,P.plug_mouth_y,8),"DF53 plug envelope / selected port",(180,-15)),
                   ((P.plug_center_x,-60,28),"Open rear channel at the root",(220,20))],
           up_axis=(0,1,0))
    render(cable_detail,drawings/"cable_strain_relief.png",(0,0,-1),
           "Grasp-side view / open saddle / cable remains outside the closed cell",
           "12 mm straight exit before R38 sweep. Release the tie before sensor service; no enclosed cable tunnel.",
           labels=[((P.plug_center_x,P.cable_start_y-8,P.cable_z),"Parallel straight leads",(180,0)),
                   ((P.plug_center_x,P.tie_y,6),"Accessible releasable tie",(180,20))],up_axis=(0,1,0))
    render(cable_detail, drawings / "cable_exit_side.png", (1,0,0),
           "Side view / straight exit first / R38 mm bend clear of the root",
           "Initial tangent is parallel to module. No immediate elbow; actual harness minimum bend radius remains unverified.",
           up_axis=(0,1,0))
    render({k:m for k,m in cables.items() if k != "original_actuator_and_transmission"},
           drawings / "service_loops.png", (0,-.4,1),
           "Service loops / provisional fixed loom ends / 50 mm travel per finger",
           "Constant cable length; loop centre moves 25 mm over full stroke; R25.7 mm loop / R25 mm fixed turn")
    render({"finger": local["replacement_finger"]}, drawings / "replacement_finger.png", (1.3, 1.8, 1.4),
           "One-piece replacement finger — print quantity 2",
           f"{P.width:g} mm wide x {P.tip_y - P.mount_y:g} mm long; 5 mm webs / partial box / 6 mm root seats / sensor bosses",
           up_axis=(0, -1, 0))
    render({"finger":local["replacement_finger"]},drawings/"reinforced_structure.png",(1.4,1.8,1.2),
           "Reinforced V2 / root collar, radiused core, partial box",
           "5 mm webs / 3.5 mm skins / 6 mm root seat / sensor bosses",up_axis=(0,-1,0))
    render({"finger":local["replacement_finger"],"key_start":cad_mesh(root_key_envelope(-6,19.25,0),AMBER),
            "key_turned":cad_mesh(root_key_envelope(-6,19.25,60),GREEN)},drawings/"root_service_access.png",(1.2,1.6,-1.4),
           "Root service window / short L-key / 60 degree inward turn",
           "Two alternative tool poses shown. Install root screws before sensor and harness; actual drive size unverified.",
           up_axis=(0,-1,0))
    render({"flange": cad_mesh(flange)}, drawings / "mounting_interface.png", (0, -1, 0),
           "Carrier interface / Y = -70 mm / axes along Y",
           "Four nominal Ø2.4 holes: X = ±6; Z = 11.25 / 19.25 mm (12 x 8 pattern). Central Ø4 access relief.",
           labels=[((-6, -70, 19.25), "M2 thread inferred; verify", (-170, -65))])
    rear = {"finger": local["replacement_finger"], "sensor": local["M2324"]}
    render(rear, drawings / "sensor_mount.png", (0, 0, 1),
           "M2324 rear mounting / screwdriver access / connector window",
           "Six holes: 17.5 mm column pitch / 8 mm row pitch. Blue rails touch the rear mounting strips only.",
           up_axis=(0, -1, 0))
    exploded = {k: m.copy() for k, m in local.items() if k in ("retained_carrier", "replacement_finger", "M2324")}
    exploded["retained_carrier"].apply_translation((0, -12, 0))
    exploded["M2324"].apply_translation((0, 0, -12))
    render(exploded, drawings / "exploded.png", (1.2, 1.6, 1.1),
           "Assembly order: carrier screws first, then sensor screws",
           "Root screws via service window first; sensor and harness last. Exploded offsets: block -12 Y; sensor -12 Z mm.", up_axis=(0, -1, 0))
    printed = cad_mesh(print_location() * finger)
    bed = trimesh.creation.box((P.root_top_z-P.carrier_z_min+10, P.tip_y-P.mount_y+10, .4))
    bed.apply_translation((-(P.root_top_z+P.carrier_z_min)/2, (P.tip_y-P.mount_y)/2, -.2))
    bed.visual.face_colors = (212, 222, 232, 255)
    render({"finger": printed, "bed": bed}, drawings / "print_orientation.png", (1.5, -1.5, 1.2),
           "Side on bed / load paths within layers / supports accessible",
           "P2S PETG: 0.4 mm nozzle / 0.2 mm layers / 8 walls / 100% infill candidate. Keep supports out of short core bridges.")
    carrier, original = carrier_and_finger(1)
    carrier.visual.face_colors, original.visual.face_colors = AMBER, GREY
    render({"carrier": carrier, "original": original}, drawings / "reference_finger.png", (1, -2, 1),
           "Original finger and separate moving block", "Amber body retained unchanged; grey finger omitted from V2 assembly", up_axis=(0, -1, 0))
    render({"carrier": carrier}, drawings / "reference_carrier.png", (0, 1, 0),
           "Retained moving block: actual supplied mesh", "Four blind pilots plus central through feature; mating face Y = -70 mm")
    # Side-by-side display offset is transverse only: the Y datum and scale are
    # identical, so printed-holder length cannot masquerade as tactile reach.
    original.apply_translation((0,0,-42))
    datum_meshes = {}
    for name,y in (("mount_plane",P.mount_y),("stock_tip_plane",0)):
        datum = trimesh.creation.box((.2,.16,85))
        datum.apply_translation((0,y,-8))
        datum.visual.face_colors = (197,73,65,255)
        datum_meshes[name] = datum
    render({"original":original, "replacement":local["replacement_finger"],
            "sensor":local["M2324"], **datum_meshes}, drawings / "reach_comparison.png", (1,0,0),
           "Original vs V2 / same longitudinal datum / 70.000 mm functional reach",
           "Red: Y=-70 mounting plane and Y=0 stock tip / V2 tactile crown. Grey stock offset 42 mm across display only.",
           labels=[((0,0,-42),"Original fingertip",(-120,-35)),
                   ((0,0,1),"V2 tactile crown",(-150,-35)),
                   ((0,-70,4),"Shared mounting plane",(-150,30))], up_axis=(0,1,0))
    (V2 / "docs/reference-measurements.json").write_text(json.dumps(reference_report(), indent=2) + "\n")
    from compare_structure import compare_structure
    compare_structure(finger)
    from verify_sensor_access import verify_sensor_access
    sensor_access = verify_sensor_access(finger,sensor,write=True)
    sources = sorted((V2 / "cad/source").glob("*.py")) + sorted((V2 / "scripts/cad").glob("*.py"))
    manifest = {"units": {"STEP": "mm", "STL": "unitless; import as mm", "GLB": "m"},
                "parameters": asdict(P), "preservation": preservation,
                "stl_tessellation_audit":stl_audit,
                "sensor_screw_access":{"status":sensor_access["status"],
                                       "actual_hardware_confirmed":False,
                                       "report":"docs/sensor-screw-access.json"},
                "environment": {name: importlib.metadata.version(name) for name in
                                ("build123d", "cadquery-ocp-novtk", "trimesh", "numpy", "scipy", "pillow")},
                "source_sha256": {str(p.relative_to(V2)): sha(p) for p in sources},
                "previous_revision_manifest_sha256":sha(V2/"docs/previous-revision.json"),
                "artifact_sha256": {str(p.relative_to(V2)): sha(p) for p in
                                    sorted(exports.iterdir()) + sorted(drawings.iterdir()) +
                                    [V2/"docs/mechanical-comparison.json",V2/"docs/section-properties.csv",V2/"docs/mechanical-comparison.md",
                                     V2/"docs/sensor-screw-access.json",V2/"docs/sensor-screw-access.md"]}}
    (V2 / "docs/build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    check_preservation()
    print(f"Generated {len(manifest['artifact_sha256'])} artifacts in {V2}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-validation", action="store_true", help="Export only during CAD iteration")
    args = parser.parse_args()
    build()
    if not args.skip_validation:
        from validate_adapter import validate
        validate()
