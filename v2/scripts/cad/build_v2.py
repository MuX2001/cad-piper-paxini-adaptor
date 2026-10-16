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
                                service_cable, strain_relief_band, root_key_envelope, box_between)
from render import render, font
from PIL import Image, ImageDraw
from sensor_fasteners import sensor_screw, cylinder, driver_components

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
    pre_counterbore = json.loads((V2/"docs/pre-counterbore-revision.json").read_text())
    access_changed = [name for name,digest in pre_counterbore["files"].items()
                      if sha(V2/pre_counterbore["snapshot"]/name) != digest]
    assert not access_changed, f"Previous reinforced V2 snapshot changed: {access_changed}"
    pre_short_pad = json.loads((V2/"docs/pre-short-pad-revision.json").read_text())
    pad_changed = [name for name,digest in pre_short_pad["files"].items()
                   if sha(V2/pre_short_pad["snapshot"]/name) != digest]
    assert not pad_changed, f"Previous long-passage V2 changed: {pad_changed}"
    pre_print = json.loads((V2/"docs/pre-printability-revision.json").read_text())
    print_changed = [name for name,digest in pre_print["files"].items()
                     if sha(V2/pre_print["snapshot"]/name) != digest]
    assert not print_changed, f"Previous short-pad V2 changed: {print_changed}"
    simplification = json.loads((V2/'docs/pre-simplification-revision.json').read_text())
    simplification_changed = [name for name,digest in simplification['files'].items()
                              if sha(V2/simplification['snapshot']/name)!=digest]
    assert not simplification_changed, simplification_changed
    return {"pre_existing_files": len(initial["files"]), "changed": changed,
            "subsequent_user_inputs": len(initial.get("subsequent_user_inputs", {})),
            "new_files_outside_v2": extra, "initial_head": initial["head"],
            "previous_v2_commit":previous["git_commit"], "previous_v2_files":len(previous["files"]),
            "previous_v2_changed":revision_changed,
            "previous_reinforced_v2_files":len(pre_counterbore["files"]),
            "previous_reinforced_v2_changed":access_changed,
            "previous_long_passage_v2_files":len(pre_short_pad["files"]),
            "previous_long_passage_v2_changed":pad_changed,
            "previous_short_pad_geometry_files":len(pre_print["files"]),
            "previous_short_pad_geometry_changed":print_changed,
            "previous_complete_reinforced_files":len(simplification['files']),
            "previous_complete_reinforced_changed":simplification_changed}


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


PREVIEW_NAMES = {'replacement_finger.png','sensor_mount.png','assembly.png',
                 'cable_routing.png','print_orientation.png'}


def make_previews(finger,sensor,local,drawings):
    # Superseded previews are retained in the complete pre-simplification archive.
    archive = json.loads((V2/'docs/pre-simplification-revision.json').read_text())
    for path in drawings.glob('*.png'):
        if path.name not in PREVIEW_NAMES:
            key = str(path.relative_to(V2))
            assert sha(V2/archive['snapshot']/key)==archive['files'][key]
            assert sha(path)==archive['files'][key], f'Unarchived image: {path}'
            path.unlink()
    render({'finger':local['replacement_finger']},drawings/'replacement_finger.png',(.7,1,2),
           'Simplified reinforced V2 / one continuous sensor plate',
           '28 x 73.2 x 27 mm   |   Solid arm, unchanged root collar, one common screw-access pocket',
           up_axis=(0,-1,0))

    # Actual B-rep close-up plus an actual section, composed in memory into one PNG.
    purple = (155,82,189,255)
    close = {'finger':cad_mesh(finger & box_between(-15,15,-24.5,4,3,35),BLUE),
             'sensor':cad_mesh(sensor,GREEN)}
    for i,(x,y) in enumerate(P.sensor_axes,1):
        close[f'S{i}'] = cad_mesh(sensor_screw(x,y),STEEL)
        close[f'axis{i}'] = cad_mesh(cylinder(x,y,P.sensor_screw_seat_z(y)+1.6,.2,9),AMBER)
    x,y = P.sensor_axes[2]
    tools = driver_components(x,y)
    tool = (tools['engaged_hex_tip']+tools['shaft']) & box_between(x-2,x+2,y-2,y+2,12,25)
    close['driver'] = cad_mesh(tool,purple)
    labels = [((x,y,23.4),f'S{i}',(-18,-28)) for i,(x,y) in enumerate(P.sensor_axes,1)]
    left = render(close,None,(.08,.15,1.8),'Common open pocket','22 x 21.7 mm / R2 / six M1.6 x 5',labels,
                  up_axis=(0,1,0),image_size=(960,940),show_footer=False)
    clip = box_between(-14,-3,y,y+.05,6,25)
    section = {name:cad_mesh(shape & clip,color) for name,shape,color in
               (('PETG',finger,BLUE),('sensor',sensor,GREEN),('screw',sensor_screw(x,y),STEEL),('driver',tool,purple))}
    right = render(section,None,(0,-1,0),'S3 section','Blue: PETG / green: sensor',
                   image_size=(480,940),show_footer=False)
    im = Image.new('RGB',(1440,1080),'#f5f7fa');im.paste(left,(0,75));im.paste(right,(960,75))
    draw = ImageDraw.Draw(im)
    draw.text((32,22),'Sensor mount / continuous planar seat / straight screw and tool access',font=font(28),fill='#142c45')
    draw.line((960,100,960,970),fill='#ccd5df',width=2)
    draw.text((995,825),'Head seat Z = 12.8',font=font(21),fill='#142c45')
    draw.text((995,865),'Sensor plane Z = 9.2',font=font(21),fill='#142c45')
    draw.text((995,910),'Pass-through: 3.6 mm',font=font(22),fill='#142c45')
    draw.text((32,1020),'Steel: seated screws   Amber: axial paths   Purple: example driver   |   Reference hardware; physical fit unverified',font=font(18),fill='#46576b')
    im.save(drawings/'sensor_mount.png')

    poses = {q:assembly_meshes(local,q,with_cable=False) for q in (0,100)}
    frame = np.vstack([m.vertices for parts in poses.values() for m in parts.values()])
    im = Image.new('RGB',(1440,1080),'#f5f7fa')
    for index,q in enumerate((0,100)):
        panel = render(poses[q],None,(1,0,.18),'Closed / q = 0 mm' if q==0 else 'Fully open / q = 100 mm',
                       f'Sensor envelope gap: {q+2*sensor.bounding_box().min.Z:.3f} mm',
                       image_size=(720,930),frame_points=frame,show_footer=False)
        im.paste(panel,(720*index,85))
    draw = ImageDraw.Draw(im)
    draw.text((32,22),'Dual-finger assembly / full gripper / identical scale',font=font(29),fill='#142c45')
    draw.text((32,1020),'Grey: original PiPER mechanism   Blue: V2   Green: M2324   |   Harness shown separately in cable_routing.png',font=font(18),fill='#46576b')
    im.save(drawings/'assembly.png')

    cable_detail = {k:v for k,v in local.items() if k in ('replacement_finger','M2324','retained_carrier')}
    cable_detail['M2324'] = cad_mesh(sensor & box_between(0,15,-24,4,0,12),GREEN)
    cable_detail.update({'plug':cad_mesh(plug_envelope(),AMBER),'leads':cad_mesh(cable_envelope(),AMBER),
                         'tie':cad_mesh(strain_relief_band(),STEEL)})
    render(cable_detail,drawings/'cable_routing.png',(.5,.3,-1.6),
           'Cable route / connector exit / accessible strain relief',
           'Sensor shown cut away to expose the connector / 12 mm straight exit, R38 turn / actual harness fit unverified',
           labels=[((P.plug_center_x,P.plug_mouth_y,8),'Parallel connector exit',(160,-30)),
                   ((P.plug_center_x,P.tie_y,6),'Releasable tie / smooth saddle',(150,25))],up_axis=(0,1,0))
    printed = cad_mesh(print_location()*finger,BLUE)
    bed = trimesh.creation.box((37,83.2,.4));bed.apply_translation((-17.5,36.6,-.2))
    bed.visual.face_colors = (212,222,232,255)
    # A small reference patch marks the upper pocket wall that needs support
    # review, not generated support geometry or validated slicer settings.
    review = box_between(10.85,10.95,-18,-1,14,18)
    render({'finger':printed,'bed':bed,'review':cad_mesh(print_location()*review,AMBER)},
           drawings/'print_orientation.png',(-1.5,-1.5,.9),
           'Side on bed / bending load paths within layers / slicing NOT VERIFIED',
           'PETG: 0.4 mm nozzle / 0.20 mm layers / 4-5 walls / 25-35% infill',
           labels=[(tuple((print_location()*review).center()),'Amber: accessible pocket support-review area',(-220,-80))])
    assert {p.name for p in drawings.glob('*.png')}==PREVIEW_NAMES


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
    make_previews(finger,sensor,local,drawings)
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
                "pre_counterbore_manifest_sha256":sha(V2/"docs/pre-counterbore-revision.json"),
                "pre_short_pad_manifest_sha256":sha(V2/"docs/pre-short-pad-revision.json"),
                "pre_printability_manifest_sha256":sha(V2/"docs/pre-printability-revision.json"),
                "pre_simplification_manifest_sha256":sha(V2/"docs/pre-simplification-revision.json"),
                "essential_previews":sorted(PREVIEW_NAMES),
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
