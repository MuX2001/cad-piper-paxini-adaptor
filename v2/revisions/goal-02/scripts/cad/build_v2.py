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
                                service_cable, strain_relief_band)
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
    return {"pre_existing_files": len(initial["files"]), "changed": changed,
            "subsequent_user_inputs": len(initial.get("subsequent_user_inputs", {})),
            "new_files_outside_v2": extra, "initial_head": initial["head"]}


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
    for name, part in parts.items():
        export_step(part, exports / f"{name}.step")
        export_stl(part, exports / f"{name}.stl", tolerance=.03, angular_tolerance=.15)
        printable = print_location() * part if name == "replacement_finger" else part
        if name == "mount_fit_gauge":
            # Flange rear on bed: new Z = old Y - mount_y.
            from build123d import Rot
            printable = Pos(0, P.carrier_z_max, -P.mount_y) * Rot(90, 0, 0) * part
        export_stl(printable, exports / f"{name}_print.stl", tolerance=.03, angular_tolerance=.15)
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
           "Cable leaves toward the base along -Y; 12 mm straight run; releasable tie away from connector",
           labels=[((P.plug_center_x,P.plug_mouth_y,8),"DF53 plug envelope / selected port",(180,-15)),
                   ((P.plug_center_x,P.cable_start_y-6,P.cable_z),"12 mm straight parallel exit",(220,0)),
                   ((P.plug_center_x,P.tie_y,12),"Release tie before unplugging",(220,20))],
           up_axis=(0,1,0))
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
           f"{P.width:g} mm wide x {P.tip_y - P.mount_y:g} mm long; four root fasteners; six sensor fasteners; twin ribs and tie slots",
           up_axis=(0, -1, 0))
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
           "Exploded offsets: retained block -12 mm Y; sensor -12 mm Z. No actuator modifications.", up_axis=(0, -1, 0))
    printed = cad_mesh(print_location() * finger)
    bed = trimesh.creation.box((34, P.tip_y-P.mount_y+10, .4))
    bed.apply_translation((-15.25, (P.tip_y-P.mount_y)/2, -.2))
    bed.visual.face_colors = (212, 222, 232, 255)
    render({"finger": printed, "bed": bed}, drawings / "print_orientation.png", (1.5, -1.5, 1.2),
           "Side on bed / load paths within layers / supports accessible",
           "P2S: candidate 0.4 mm nozzle, 0.2 mm layers. Support the upper rail/window span; full-part print hold applies.")
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
    sources = sorted((V2 / "cad/source").glob("*.py")) + sorted((V2 / "scripts/cad").glob("*.py"))
    manifest = {"units": {"STEP": "mm", "STL": "unitless; import as mm", "GLB": "m"},
                "parameters": asdict(P), "preservation": preservation,
                "environment": {name: importlib.metadata.version(name) for name in
                                ("build123d", "cadquery-ocp-novtk", "trimesh", "numpy", "scipy", "pillow")},
                "source_sha256": {str(p.relative_to(V2)): sha(p) for p in sources},
                "artifact_sha256": {str(p.relative_to(V2)): sha(p) for p in
                                    sorted(exports.iterdir()) + sorted(drawings.iterdir())}}
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
