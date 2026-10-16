"""Focused geometric checks for V2, plus read-only V1 regression and preservation."""

import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / "cad/source"))

import numpy as np
import trimesh
from build123d import Plane, Pos, Rot, Solid, import_step
from PIL import Image
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

from build_v2 import (ROOT, assembly_meshes, check_preservation, local_meshes, sha)
from references import (GRIPPER, carrier_and_finger, faceted_solid, jaw_matrix,
                        mating_holes, sensor_mounting_axes, vendor_mesh,
                        reach_measurements, connector_measurements)
from replacement_finger import (P, bore, box_between, cable_envelope, hardware, jaw_location, make_coupon,
                                make_finger, make_flange, placed_sensor, plug_envelope, print_location,
                                moving_cable_path, service_cable_path, service_cable, strain_relief_band,
                                root_key_envelope)


def overlap(a, b):
    # Strictly separated bounding boxes prove zero volume without a costly
    # sensor B-rep boolean. Touching/overlapping boxes still use exact solids.
    aa, bb = a.bounding_box(), b.bounding_box()
    if np.any(np.array(tuple(aa.min)) > np.array(tuple(bb.max)) + 1e-6) or np.any(
            np.array(tuple(bb.min)) > np.array(tuple(aa.max)) + 1e-6):
        return 0.0
    common = a & b
    return 0.0 if common is None else float(common.volume)


def zero_overlap(a, b, name, results):
    value = overlap(a, b)
    assert value < .001, f"{name}: {value} mm^3 interference"
    results[name] = value


def check_reach(finger):
    measured = reach_measurements()
    previous = json.loads((V2/"revisions/goal-02/docs/validation.json").read_text())
    crown_native = measured["sensor_crown_native_y_mm"]
    crown_y = [P.sensor_y_translation - crown_native[1], P.sensor_y_translation - crown_native[0]]
    for stock in measured["stock"]:
        assert abs(crown_y[1] - stock["tip_y_mm"]) < .01
        assert crown_y[0] < stock["contact_y_mm"][0]
    assert abs(finger.bounding_box().max.Y - P.tip_y) < 1e-5
    return {"measurement": measured, "original_reach_mm": measured["stock"][0]["reach_mm"],
            "corrected_tactile_reach_mm": crown_y[1] - P.mount_y,
            "corrected_tactile_contact_from_mount_mm": [v-P.mount_y for v in crown_y],
            "previous_v2_tactile_reach_mm": previous["functional_reach"]["corrected_tactile_reach_mm"],
            "early_goal01_tactile_reach_mm": -39-crown_native[0]-P.mount_y,
            "holder_length_mm": P.tip_y-P.mount_y, "holder_width_mm": P.width,
            "reinforcement": "5 mm webs, 3.5 mm skins, partial closed cell, 6 mm root seats, 27 mm root depth and radiused transitions",
            "load_or_deflection_tested": False}


def check_cable(finger, sensor, screws, interference):
    mouths = connector_measurements()
    mouth = min(mouths, key=lambda m: abs(m["mouth_x_mm"]-P.plug_center_x))
    assert abs(mouth["mouth_x_mm"]-P.plug_center_x) < 1e-5
    assert abs(mouth["mouth_y_mm"]-P.socket_mouth_native_y) < 1e-5
    moving = moving_cable_path()
    assert np.allclose(tuple(moving.tangent_at(0)), mouth["exit_jaw"], atol=1e-6)
    assert abs(moving.edges()[0].length-P.straight_exit) < 1e-6
    local_cables = {"catalog_exposed_plug": plug_envelope(), "moving_lead_envelope": cable_envelope(),
                    "releasable_tie": strain_relief_band()}
    for name, shape in local_cables.items():
        assert shape.is_valid and len(shape.solids()) == 1
        for key, rigid in {"finger":finger, "sensor":sensor, **screws}.items():
            zero_overlap(rigid, shape, f"{key}_vs_{name}", interference)
    # Straight unplugging corridor: withdraw 8 mm along the actual port axis.
    plug = local_cables["catalog_exposed_plug"]
    bounds = plug.bounding_box()
    withdrawal = box_between(bounds.min.X,bounds.max.X,bounds.min.Y-8,bounds.max.Y,bounds.min.Z,bounds.max.Z)
    for key, rigid in {"finger":finger, **screws}.items():
        zero_overlap(rigid, withdrawal, f"{key}_vs_parallel_unplug_corridor", interference)
    # A full rectangular maximum envelope is not the actual stepped plug.
    # Record its vendor-housing sweep conflict rather than silently moving
    # the plug away from the measured socket or claiming verified unplugging.
    vendor_withdrawal_overlap = overlap(sensor,withdrawal)
    lengths, endpoints = [], []
    for opening in range(101):
        path = service_cable_path(opening)
        lengths.append(path.length)
        endpoints.append(tuple(path.position_at(1)))
        expected_start = jaw_matrix(1,opening) @ np.r_[tuple(moving.position_at(1)),1]
        assert np.allclose(tuple(path.position_at(0)),expected_start[:3],atol=1e-6)
        assert np.allclose(tuple(path.tangent_at(0)),(0,-1,0),atol=1e-6)
        edges = path.edges()
        for first, second in zip(edges,edges[1:]):
            assert np.allclose(tuple(first.position_at(1)),tuple(second.position_at(0)),atol=1e-6)
            assert np.allclose(tuple(first.tangent_at(1)),tuple(second.tangent_at(0)),atol=1e-6)
    assert np.ptp(lengths) < 1e-6 and np.max(np.ptp(endpoints,axis=0)) < 1e-6
    assert P.loop_turn_u_closed-P.cable_z-P.cable_bend_radius-25 > 0
    return {"native_mouths":mouths,"chosen_port_x_mm":P.plug_center_x,
            "catalog_exposed_plug_mm":[P.plug_width,P.plug_exposed_length,P.plug_height],
            "assumed_loose_lead_envelope_mm":[P.cable_width,P.cable_thickness],
            "initial_direction_jaw":[0,-1,0],"straight_exit_mm":P.straight_exit,
            "centreline_radii_mm":[P.cable_bend_radius,P.loop_radius,P.fixed_turn_radius],
            "minimum_inner_envelope_radius_mm":min(P.cable_bend_radius-P.cable_thickness/2,
                  P.loop_radius-P.cable_width/2,P.fixed_turn_radius-P.cable_thickness/2),
            "manufacturer_minimum_bend_radius_mm":P.manufacturer_min_bend_radius,
            "holder_straight_withdrawal_corridor_mm":8,
            "full_box_withdrawal_vs_vendor_housing_mm3":vendor_withdrawal_overlap,
            "actual_plug_unmating_verified":False,
            "withdrawal_limit":"Printed holder and hardware clear 8 mm straight corridor. Conservative full rectangular plug box clips vendor housing during withdrawal; actual stepped plug geometry/latch must be checked. No socket displacement assumed.",
            "moving_path_length_mm":moving.length,
            "service_path_length_mm":lengths[0],"combined_path_length_mm":moving.length+lengths[0],
            "length_variation_over_101_openings_mm":float(np.ptp(lengths)),
            "fixed_endpoint_side1_mm":endpoints[0],"fixed_endpoint_side2_mm":[-endpoints[0][0],-endpoints[0][1],endpoints[0][2]],
            "minimum_outbound_straight_leg_mm":P.loop_turn_u_closed-P.cable_z-P.cable_bend_radius-25,
            "loop_translation_over_full_stroke_mm":25,"fixed_loom_restraint_physical_fit_verified":False,
            "physical_harness_and_port_selection_verified":False}


def validate():
    report = {"status": "running", "physical_validation": False, "full_print_release": False,
              "units": "mm", "parts": {}, "interference_mm3": {}, "opening_checks": {}}
    report["preservation"] = check_preservation()
    manifest = json.loads((V2 / "docs/build-manifest.json").read_text())
    for kind in ("source_sha256", "artifact_sha256"):
        for name, digest in manifest[kind].items():
            assert sha(V2 / name) == digest, f"Stale build: {name}; regenerate"
    assert sha(V2/"docs/previous-revision.json") == manifest["previous_revision_manifest_sha256"]

    finger, sensor = make_finger(), placed_sensor()
    screws = hardware()
    report["functional_reach"] = check_reach(finger)
    mechanical = json.loads((V2/"docs/mechanical-comparison.json").read_text())
    assert mechanical["status"] == "comparative_calculation_passed"
    assert abs(mechanical["reinforced"]["volume_mm3"]-finger.volume) < .01
    assert mechanical["ratios"]["grip_stiffness"] > 1.5 and mechanical["ratios"]["lateral_stiffness"] > 1
    assert mechanical["ratios"]["root_nominal_stress"] < 1
    from compare_structure import section_properties
    for stored in mechanical["reinforced"]["section_samples"]:
        measured = section_properties(finger,stored["y_mm"])
        for key in ("area_mm2","Ixx_mm4","Izz_mm4"):
            assert abs(measured[key]-stored[key]) < .01
    radii = {round(s.Cylinder().Radius(),6) for face in finger.faces()
             if (s:=BRepAdaptor_Surface(face.wrapped)).GetType() == GeomAbs_Cylinder}
    assert {P.core_fillet,P.transition_fillet,P.service_window_radius}.issubset(radii)
    report["mechanical_comparison"] = {"status":mechanical["status"],"ratios":mechanical["ratios"],
        "section_properties_rechecked":True,"fillet_radii_present_mm":[2,2.5,3],
        "physical_strength_verified":False,"report":"docs/mechanical-comparison.json"}
    parts = {"replacement_finger": finger, "mount_fit_gauge": make_flange(), "fastener_coupon": make_coupon()}
    for name, part in parts.items():
        assert part.is_valid and len(part.solids()) == 1
        path = V2 / "cad/exported" / name
        step = import_step(path.with_suffix(".step"))
        assert step.is_valid and len(step.solids()) == 1
        assert abs(step.volume - part.volume) < .01
        meshes = [trimesh.load_mesh(path.with_suffix(".stl")),
                  trimesh.load_mesh(path.with_name(name + "_print.stl"))]
        for mesh in meshes:
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
            assert abs(mesh.volume - part.volume) / part.volume < .005
        expected = part
        if name == "replacement_finger":
            expected = print_location() * part
        elif name == "mount_fit_gauge":
            expected = Pos(0, P.carrier_z_max, -P.mount_y) * Rot(90, 0, 0) * part
        expected_bounds = np.array([tuple(expected.bounding_box().min), tuple(expected.bounding_box().max)])
        assert np.allclose(meshes[1].bounds, expected_bounds, atol=.002)
        assert abs(meshes[1].bounds[0, 2]) < .001 and np.all(meshes[1].extents < 256)
        # Verify the intended proper rigid transform on the actual STL vertices.
        from scipy.spatial import cKDTree
        vertices = meshes[0].vertices.copy()
        if name == "replacement_finger":
            vertices = np.c_[-vertices[:, 2], vertices[:, 1] - P.mount_y, vertices[:, 0] + P.width / 2]
        elif name == "mount_fit_gauge":
            vertices = np.c_[vertices[:, 0], P.carrier_z_max - vertices[:, 2], vertices[:, 1] - P.mount_y]
        assert cKDTree(meshes[1].vertices).query(vertices)[0].max() < .005
        assert cKDTree(vertices).query(meshes[1].vertices)[0].max() < .005
        report["parts"][name] = {"valid_single_STEP_solid": True, "watertight_single_STL_body": True,
                                  "cad_volume_mm3": part.volume, "print_bounds_mm": meshes[1].bounds.tolist(),
                                  "stl_volume_relative_error": abs(meshes[0].volume - part.volume) / part.volume,
                                  "bed_z_mm": float(meshes[1].bounds[0, 2])}
    print("STEP/STL: 3 valid solids, watertight meshes, print orientations on bed", flush=True)

    urdf = ET.parse(GRIPPER / "urdf/agx_gripper_description.urdf").getroot()
    master = urdf.find("joint[@name='gripper']/limit")
    assert float(master.attrib["lower"]) == 0 and float(master.attrib["upper"]) == .1
    for side in (1, 2):
        joint = urdf.find(f"joint[@name='gripper_joint{side}']")
        origin = np.fromstring(joint.find("origin").attrib["xyz"], sep=" ") * 1000
        assert np.allclose(origin, (0, 0, 138))
        from trimesh.transformations import euler_matrix
        rotation = euler_matrix(*np.fromstring(joint.find("origin").attrib["rpy"], sep=" "))[:3, :3]
        assert np.allclose(rotation, jaw_matrix(side, 0)[:3, :3], atol=1e-6)
        assert float(joint.find("mimic").attrib["multiplier"]) == (.5 if side == 1 else -.5)
        carrier, _ = carrier_and_finger(side)
        holes = [h for h in mating_holes(carrier) if abs(h["x"]) > 1]
        expected = sorted((x, z) for x in P.mount_hole_x for z in P.mount_hole_z)
        measured = sorted((h["x"], h["z"]) for h in holes)
        # Sorting with rounded keys avoids insignificant x roundoff reordering rows.
        measured = sorted(measured, key=lambda xz: tuple(round(x, 3) for x in xz))
        assert np.allclose(measured, expected, atol=1e-4)
        assert max(h["max_fit_residual_mm"] for h in holes) < 1e-4
        zero_overlap(finger, faceted_solid(carrier), f"finger_vs_retained_carrier_{side}", report["interference_mm3"])
        assert abs(carrier.bounds[1, 1] - P.mount_y) < 1e-4
    assert np.allclose(sensor_mounting_axes(), sorted((x, y) for x in P.sensor_hole_x for y in P.sensor_hole_y), atol=1e-5)
    assert abs(sensor.bounding_box().max.Z - P.sensor_rear_z) < 1e-5
    report["interfaces"] = {"both_carrier_patterns_match": True, "root_pattern_mm": [12, 8],
                             "sensor_six_axes_match_STEP": True, "sensor_rear_z_mm": P.sensor_rear_z,
                             "stock_fingers_removed_as_whole_bodies": True,
                             "thread_type_and_physical_removal_verified": False}
    zero_overlap(finger, sensor, "finger_vs_sensor", report["interference_mm3"])
    for name, screw in hardware().items():
        zero_overlap(finger, screw, f"finger_vs_{name}", report["interference_mm3"])
    for x in P.mount_hole_x:
        for z in P.mount_hole_z:
            # Full annular head seat for the entire 6 mm bearing thickness.
            bearing = bore((x,P.mount_y,z),(0,1,0),P.mount_head_diameter,P.flange_thickness)
            bearing -= bore((x,P.mount_y-.1,z),(0,1,0),P.mount_bore,P.flange_thickness+.2)
            assert abs(bearing.volume-overlap(finger,bearing)) < .001
            head_insertion = bore((x,P.flange_front_y,z),(0,1,0),P.mount_head_diameter,
                                  P.root_head_access_end_y+1-P.flange_front_y)
            zero_overlap(finger,head_insertion,f"root_head_insertion_{x}_{z}",report["interference_mm3"])
            for angle in range(0,61,5):
                tool = root_key_envelope(x,z,angle)
                zero_overlap(finger,tool,f"root_L_key_{x}_{z}_{angle}_vs_finger",report["interference_mm3"])
                zero_overlap(sensor,tool,f"root_L_key_{x}_{z}_{angle}_vs_sensor",report["interference_mm3"])
    for x, y in P.sensor_axes:
        # 3 mm head-bearing annulus, excluding the intentional bore-mouth
        # chamfer that clears the catalog screw's maximum under-head blend.
        annulus = bore((x, y, P.sensor_screw_seat_z - 2), (0, 0, 1), 3.0, 2)
        annulus -= bore((x, y, P.sensor_screw_seat_z - 2.1), (0, 0, 1), P.sensor_bore, 2.2)
        annulus -= Solid.make_cone(P.sensor_bore/2,P.sensor_bore/2+P.sensor_seat_chamfer,
                                  P.sensor_seat_chamfer,
                                  Plane(origin=(x,y,P.sensor_screw_seat_z-P.sensor_seat_chamfer)))
        assert abs(annulus.volume - overlap(annulus, finger)) < .001
        tool = bore((x, y, P.sensor_screw_seat_z + P.sensor_head_height), (0, 0, 1), 2.2, 30)
        zero_overlap(finger, tool, f"sensor_driver_{x}_{y}_vs_finger", report["interference_mm3"])
    # Whole conservative sensor bounding box can translate toward the grasping
    # gap without catching the new bosses or enclosure. Remove its screws first.
    sb = sensor.bounding_box()
    removal = box_between(sb.min.X,sb.max.X,sb.min.Y,sb.max.Y,sb.min.Z-12,sb.max.Z)
    zero_overlap(finger,removal,"sensor_removal_12mm_bbox_vs_finger",report["interference_mm3"])
    report["fasteners"] = {"mount_candidate": f"8 total M2 x {P.mount_screw_length:g}; verify pitch/head and real carrier thread depth",
                            "mount_nominal_penetration_mm": P.mount_screw_length - P.flange_thickness,
                            "root_bearing_thickness_mm":P.flange_thickness,
                            "root_bearing_annuli_complete":True,
                            "root_tool_access":"Short L-key through service window; 0..60 degree inward swing sampled every 5 degrees; roots fitted before harness",
                            "sensor_candidate": "12 total M1.6 x 4",
                            "sensor_nominal_penetration_mm": P.sensor_screw_length - (P.rail_thickness - P.sensor_head_recess),
                            "sensor_bearing_annuli_supported_below_seat_relief": True,
                            "sensor_seat_relief_45_deg_mm":P.sensor_seat_chamfer,
                            "sensor_removal_clearance_translation_mm":12,
                            "thread_engagement_intersections_excluded": "Nominal threaded shafts intentionally enter pilot/minor-diameter material"}
    from dataclasses import asdict
    from sensor_fasteners import S
    access = json.loads((V2/"docs/sensor-screw-access.json").read_text())
    assert access["hardware"]==asdict(S)
    assert access["status"]=="reference_geometry_passed_actual_hardware_unverified"
    assert abs(access["finger_volume_mm3"]-finger.volume)<.01
    assert len(access["screws"])==6
    for row,(x,y) in zip(access["screws"],P.sensor_axes):
        assert np.allclose(row["jaw_xy_mm"],(x,y),atol=1e-8)
        assert row["reference_geometry_status"]=="PASS" and row["overall_status"]=="UNVERIFIED"
        assert row["seating"]["after_overlap_mm3"]<1e-7
        assert row["insertion"]["unexpected_sensor_overlap_mm3"]<1e-7
        assert row["clearance_mm"]["minimum_free_surface"]>0
    report["sensor_screw_access"]={"status":access["status"],"positions_checked":6,
        "jaw_instances_checked":2,"report":"docs/sensor-screw-access.json",
        "minimum_free_surface_clearance_mm":min(r["clearance_mm"]["minimum_free_surface"] for r in access["screws"]),
        "actual_hardware_confirmed":False}
    report["cable"] = check_cable(finger,sensor,screws,report["interference_mm3"])
    previous_validation = json.loads((V2/"revisions/goal-02/docs/validation.json").read_text())
    assert abs(report["cable"]["full_box_withdrawal_vs_vendor_housing_mm3"]-
               previous_validation["cable"]["full_box_withdrawal_vs_vendor_housing_mm3"]) < 1e-6
    print("70 mm tactile reach, interfaces, tool access, parallel exit and constant cable length pass", flush=True)

    base = vendor_mesh("gripper_base")
    local = local_meshes(finger, sensor)
    moving_parts = {"finger":finger,"sensor":sensor,"plug":plug_envelope(),
                    "moving_leads":cable_envelope(),"tie":strain_relief_band(),**screws}
    design_min_z = min(s.bounding_box().min.Z for s in moving_parts.values())
    base_clearances = {}
    for name, part in moving_parts.items():
        base_clearances[name] = float(138 + part.bounding_box().min.Y - base.bounds[1, 2])
    assert min(base_clearances.values()) > 1
    report["base_z_envelope_clearances_mm"] = base_clearances
    report["continuous_motion_proof"] = {
        "range_commanded_opening_mm": [0, 100],
        "opposing_rigid_envelope_gap_formula_mm": f"opening + {2 * design_min_z:.9f}",
        "minimum_gap_mm": float(2 * design_min_z),
        "method": "Pure translations +/-opening/2 along base Y; all rigid new parts on their own side of the gap; constant Z separates them from unchanged base",
        "scope": "New fingers, sensors, fasteners, plugs, ties and moving leads. Service loops checked separately; retained mechanism unchanged."}
    base_box = box_between(*base.bounds[:,0],*base.bounds[:,1],*base.bounds[:,2])
    carriers = {side:faceted_solid(carrier_and_finger(side)[0]) for side in (1,2)}
    for opening in (0, 25, 50, 75, 100):
        a, b = jaw_location(1, opening), jaw_location(2, opening)
        overlaps = {}
        for n1, shape1 in (("finger", finger), ("sensor", sensor)):
            for n2, shape2 in (("finger", finger), ("sensor", sensor)):
                zero_overlap(a * shape1, b * shape2, f"{n1}_1_vs_{n2}_2", overlaps)
        service = {side:service_cable(side,opening) for side in (1,2)}
        for side, loop in service.items():
            assert loop.is_valid and len(loop.solids()) == 1
            zero_overlap(loop,base_box,f"loop_{side}_vs_base_bbox",overlaps)
            for jaw in (1,2):
                location = jaw_location(jaw,opening)
                for name,shape in {**moving_parts,"retained_carrier":carriers[jaw]}.items():
                    zero_overlap(loop,location*shape,f"loop_{side}_vs_{name}_{jaw}",overlaps)
            for name in ("plug","moving_leads","tie"):
                zero_overlap(moving_parts[name],carriers[side],f"{name}_vs_carrier_{side}",overlaps)
        zero_overlap(service[1],service[2],"opposing_service_loops",overlaps)
        normals = [jaw_matrix(side, opening)[:3, :3] @ (0, 0, -1) for side in (1, 2)]
        assert np.allclose(normals, ((0, 1, 0), (0, -1, 0)))
        report["opening_checks"][str(opening)] = {"conservative_gap_mm": opening + 2 * design_min_z,
                                                   "intersection_volumes_mm3": overlaps, "opposed_normals": True,
                                                   "service_loop_side1_bounds_mm":[tuple(service[1].bounding_box().min),tuple(service[1].bounding_box().max)]}
    horizontal_z_min = 138+P.bend_start_y-P.cable_bend_radius-P.cable_thickness/2
    fixed_x_clearance = abs(P.fixed_loom_x)-P.cable_width/2-max(abs(base.bounds[:,0]))
    assert horizontal_z_min > base.bounds[1,2] and fixed_x_clearance > 0
    report["continuous_service_loop_proof"] = {
        "range_mm":[0,100],"horizontal_loop_min_base_z_mm":horizontal_z_min,
        "horizontal_loop_above_base_mm":float(horizontal_z_min-base.bounds[1,2]),
        "fixed_descending_leg_outside_base_x_mm":float(fixed_x_clearance),
        "minimum_loop_turn_beyond_rigid_finger_y_mm":P.loop_turn_u_closed-25-P.root_top_z,
        "method":"Straight leg changes cancel (+q/4 and -q/4); fixed endpoints and tangent continuity checked at 101 openings. Loops stay above actuator; descending tails stay outside its X bounds. Outbound loops stay beyond their moving fingers; return legs are outside their X bounds.",
        "assumption":"Harness follows the modeled loops, with provisional fixed loom restraints at the recorded endpoints; no dynamic cable simulation or physical flex test."}
    for opening in (0, 50, 100):
        scene = trimesh.load(V2 / f"cad/exported/assembly_open{opening}.glb", force="scene")
        expected = assembly_meshes(local, opening)
        assert set(scene.geometry) == set(expected), "Missing/extra assembly components"
        for name, mesh in scene.geometry.items():
            assert np.allclose(mesh.bounds * 1000, expected[name].bounds, atol=.003), (opening, name)
            assert len(mesh.faces) == len(expected[name].faces)
            assert cKDTree(expected[name].vertices).query(mesh.vertices * 1000)[0].max() < .003
            assert cKDTree(mesh.vertices * 1000).query(expected[name].vertices)[0].max() < .003
    cable_scene = trimesh.load(V2 / "cad/exported/assembly_open50_cable_study.glb", force="scene")
    assert set(cable_scene.geometry) == set(assembly_meshes(local, 50, with_cable=True))
    pair = import_step(V2 / "cad/exported/finger_sensor_pair_open50.step")
    assert pair.is_valid and len(pair.solids()) == 6
    expected_volume = 2 * (finger.volume + sensor.volume + carrier_and_finger(1)[0].volume)
    assert abs(pair.volume - expected_volume) < .01
    expected_step = {}
    for side in (1, 2):
        for name, shape in (("replacement_finger", finger), ("M2324", sensor),
                            ("retained_carrier_faceted", faceted_solid(carrier_and_finger(side)[0]))):
            expected_step[f"{name}_{side}"] = jaw_location(side, 50) * shape
    assert {child.label for child in pair.children} == set(expected_step)
    for child in pair.children:
        shape = expected_step[child.label]
        assert abs(child.volume - shape.volume) < .01
        assert np.allclose(tuple(child.bounding_box().min), tuple(shape.bounding_box().min), atol=.001)
        assert np.allclose(tuple(child.bounding_box().max), tuple(shape.bounding_box().max), atol=.001)
    cable_step = import_step(V2 / "cad/exported/cable_routing_open50.step")
    assert cable_step.is_valid and len(cable_step.solids()) == 8
    expected_cables = {}
    for side in (1,2):
        for name,shape in (("DF53_exposed_plug",plug_envelope()),("moving_harness_envelope",cable_envelope()),
                           ("releasable_tie_envelope",strain_relief_band())):
            expected_cables[f"{name}_{side}"] = jaw_location(side,50)*shape
        expected_cables[f"service_loop_envelope_{side}"] = service_cable(side,50)
    assert {child.label for child in cable_step.children} == set(expected_cables)
    for child in cable_step.children:
        shape = expected_cables[child.label]
        assert abs(child.volume-shape.volume) < .01
        assert np.allclose(tuple(child.bounding_box().min),tuple(shape.bounding_box().min),atol=.001)
        assert np.allclose(tuple(child.bounding_box().max),tuple(shape.bounding_box().max),atol=.001)
    report["assembly"] = {"GLB_components": len(expected), "openings_mm": [0, 50, 100],
                           "complete_original_actuator_in_GLB": True, "no_stock_finger_in_GLB": True,
                           "STEP_pair_solids": 6, "cable_STEP_solids":8,"STEP_actuator_included": False}
    for path in (V2 / "drawings").glob("*.png"):
        with Image.open(path) as im:
            assert im.size == (1440, 1080)
            im.verify()
    report["previews"] = {"png_count": len(list((V2 / "drawings").glob("*.png"))),
                           "automated_check": "Readable 1440 x 1080 PNGs; visual review is separate"}
    print("Motion: 0..100 mm analytic separation and five B-rep configurations pass", flush=True)

    report["V1_regression"] = {}
    for profile in ("m2324-reference", "m2324-v2"):
        command = [sys.executable, str(ROOT / "scripts/cad/validate_adapter.py"), "--profile", profile]
        result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                text=True, capture_output=True, check=False)
        (V2 / f"docs/legacy-{profile}-validation.txt").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, f"Read-only V1 regression failed: {result.stderr[-1000:]}"
        report["V1_regression"][profile] = {"exit_code": 0, "source_or_exports_regenerated": False}
    report["preservation"] = check_preservation()
    report["status"] = "passed"
    report["build_manifest_sha256"] = sha(V2 / "docs/build-manifest.json")
    report["limitations"] = ["CAD-derived interfaces, not physical metrology; M2 pitch and usable engagement unverified",
                              "Parallel socket exit is CAD-derived; actual harness dimensions, minimum bend radius, fixed restraints and IN/OUT selection remain physically unverified",
                              "Full rectangular plug withdrawal envelope clips vendor sensor housing; actual stepped plug/latch access remains unverified although the printed holder and screws clear the corridor",
                              "Constant-length cable clearance envelope is geometric; no dynamic flex, strain or abrasion simulation",
                              "Structural results are comparative ideal-beam estimates; actual PETG properties, bolted-joint compliance, shear, local notch stresses, creep and fatigue remain unverified",
                              "No slicing, printing, strength, torque, load or powered motion tests; PRINT-HOLD remains"]
    (V2 / "docs/validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: V2 geometry; both V1 regressions; {report['preservation']['pre_existing_files']} original files unchanged", flush=True)
    return report


if __name__ == "__main__":
    validate()
