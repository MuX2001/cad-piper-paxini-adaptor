"""Explicit six-screw insertion, seating and driver checks on the complete V2.

Catalog hardware is a reference, not confirmation of supplied hardware.
Millimetres throughout; all access paths point outward along native jaw +Z.
"""

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(V2/"cad/source"))

import numpy as np
from build123d import Color, Compound, Pos, export_step, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Torus

from references import (SENSOR, cad_mesh, carrier_and_finger, faceted_solid,
                        sensor_native, vendor_mesh)
from replacement_finger import (P, bore, box_between, cable_envelope, hardware, jaw_location,
                                make_finger, placed_sensor, plug_envelope, service_cable, strain_relief_band)
from sensor_fasteners import (S, cylinder, driver_components, driver_sweeps, sensor_screw,
                              screw_insertion_sweep, for_position)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def volume_common(a,b):
    common = a & b
    return 0.0 if common is None else float(common.volume)


def clearance(a,b):
    aa,bb = a.bounding_box(),b.bounding_box()
    gap = np.maximum(0,np.maximum(np.array(tuple(aa.min))-tuple(bb.max),
                                  np.array(tuple(bb.min))-tuple(aa.max)))
    if np.linalg.norm(gap) > 1e-6:
        return {"interference_mm3":0.0,"clearance_mm":float(np.linalg.norm(gap)),
                "method":"conservative bounding-box separation lower bound"}
    return {"interference_mm3":volume_common(a,b),"clearance_mm":float(a.distance_to(b)),
            "method":"exact B-rep distance and volume; zero distance may be intentional contact"}


def non_seating_faces(finger):
    faces = []
    for face in finger.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        seat = (surface.GetType()==GeomAbs_Plane
                and abs(abs(surface.Plane().Axis().Direction().Z())-1)<1e-8
                and any(abs(surface.Plane().Location().Z()-P.sensor_screw_seat_z(y))<1e-8
                        for _,y in P.sensor_axes))
        if not seat:
            faces.append(face)
    return Compound(children=faces)


def measured_hole(x,native_y):
    faces = []
    for face in sensor_native().faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()!=GeomAbs_Cylinder:
            continue
        cyl = surface.Cylinder();point = cyl.Axis().Location()
        if abs(point.X()-x)<1e-5 and abs(point.Y()-native_y)<1e-5 and abs(cyl.Axis().Direction().Z())>.999:
            faces.append((cyl.Radius(),face.bounding_box()))
    assert len(faces)==2 and all(abs(r-.625)<1e-6 for r,_ in faces)
    lo,hi = min(b.min.Z for _,b in faces),max(b.max.Z for _,b in faces)
    assert abs(lo+2.05)<1e-6 and abs(hi+.05)<1e-6
    return {"type":"blind M1.6 tapped hole: supplied manual PDF p.8",
            "cad_minor_diameter_mm":2*faces[0][0],"cad_minor_cylinder_native_z_mm":[lo,hi],
            "cad_minor_cylinder_length_mm":hi-lo,"manual_depth_mm":S.tapped_depth_manual,
            "pitch_mm":S.pitch,"pitch_basis":"standard coarse pitch; no helix in sensor STEP",
            "physical_thread_and_full_flank_depth":"UNVERIFIED"}


def pocket_lip_z(finger,x,y):
    ends = []
    for face in finger.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()==GeomAbs_Cylinder:
            cyl = surface.Cylinder();point = cyl.Axis().Location()
            if (abs(point.X()-x)<1e-5 and abs(point.Y()-y)<1e-5
                and abs(cyl.Radius()-P.sensor_head_pocket/2)<1e-5
                and abs(cyl.Axis().Direction().Z())>.999):
                ends.append(face.bounding_box().max.Z)
    assert ends
    return max(ends)


def verify_sensor_access(finger=None,sensor=None,write=False):
    finger = make_finger() if finger is None else finger
    sensor = placed_sensor() if sensor is None else sensor
    archive = json.loads((V2/"docs/pre-counterbore-revision.json").read_text())
    before = import_step(V2/archive["snapshot"]/"cad/exported/replacement_finger.step")
    # Exact boolean comparison: all edits confined to the six local pads.
    zones = Compound(children=[cylinder(x,y,P.sensor_rear_z-1,P.sensor_boss_diameter+.002,
                                       P.root_top_z+2) for x,y in P.sensor_axes])
    removed,added = before-finger,finger-before
    outside_removed = volume_common(removed,before-zones)
    outside_added = volume_common(added,finger-zones)
    assert max(outside_removed,outside_added)<1e-6
    protected = box_between(-15,15,P.mount_y-1,P.sensor_frame_proximal_y,0,40)
    assert volume_common(removed,protected)+volume_common(added,protected)<1e-6
    # A uniform radial undersize sensitivity, not an asserted printer accuracy.
    tolerance_p = replace(P,sensor_bore=P.sensor_bore-2*P.sensor_print_radial_error,
                           sensor_head_pocket=P.sensor_head_pocket-2*P.sensor_print_radial_error)
    tolerance_finger = make_finger(tolerance_p)
    tolerance_walls = non_seating_faces(tolerance_finger)
    walls = non_seating_faces(finger)
    screws = hardware()
    carriers = {side:faceted_solid(carrier_and_finger(side)[0]) for side in (1,2)}
    base = vendor_mesh("gripper_base")
    base_box = box_between(*base.bounds[:,0],*base.bounds[:,1],*base.bounds[:,2])
    local = {"finger":finger,"sensor":sensor,**screws,"plug":plug_envelope(),
             "leads":cable_envelope(),"tie":strain_relief_band()}
    records = []
    for i,(x,y) in enumerate(P.sensor_axes,1):
        name = f"S{i}"
        spec = for_position(y)
        seat = P.sensor_screw_seat_z(y)
        screw = sensor_screw(x,y)
        insertion = screw_insertion_sweep(x,y)
        tools = driver_sweeps(x,y)
        components = driver_components(x,y)
        assert seat-spec.length_max+S.insertion_travel > finger.bounding_box().max.Z
        # Exempt ONLY the coaxial major-diameter volume inside the documented
        # tapped depth. A helix-free vendor pilot is not a clearance hole.
        intended_thread = cylinder(x,y,P.sensor_rear_z-S.tapped_depth_manual,
                                   S.diameter+2e-6,S.tapped_depth_manual+1e-6)
        sensor_outside_thread = sensor-intended_thread
        raw_thread_overlap = volume_common(insertion,sensor)
        unexpected_sensor_overlap = volume_common(insertion,sensor_outside_thread)
        insertion_check = clearance(insertion,finger)
        driver_checks = {key:clearance(shape,finger) for key,shape in tools.items()}
        seating_after = volume_common(screw,finger)
        curved_clearance = {}
        for face in screw.faces():
            surface = BRepAdaptor_Surface(face.wrapped)
            if surface.GetType()==GeomAbs_Torus:
                curved_clearance["underhead_blend"] = float(face.distance_to(walls))
            elif surface.GetType()==GeomAbs_Cylinder:
                key = "head_wall" if surface.Cylinder().Radius()>1 else "shaft_wall"
                curved_clearance[key] = float(face.distance_to(walls))
        assert len(curved_clearance)==3
        # Minimum ISO bearing diameter; relief is excluded from the flat seat.
        bearing = cylinder(x,y,seat-.05,S.bearing_diameter_min,.05)
        bearing -= cylinder(x,y,seat-.1,
                            P.sensor_bore+2*P.sensor_seat_chamfer,.15)
        assert abs(bearing.volume-volume_common(bearing,finger))<1e-7
        # Nominal hex engagement including the socket floor contact; the tool
        # and screw rotate together. Do not rotate a round tip inside the socket.
        engaged_driver = components["engaged_hex_tip"]+components["shaft"]
        tool_vs_own_screw = volume_common(engaged_driver,screw)
        mechanism_checks = {}
        # Both real jaw transforms, both retained blocks, all installed screws,
        # opposite sensor/finger and complete source actuator bounding envelope.
        for opening in (0,50,100):
            for side in (1,2):
                location = jaw_location(side,opening)
                obstacles = {"actuator_conservative_bbox":base_box,
                             "service_loop_1":service_cable(1,opening),"service_loop_2":service_cable(2,opening)}
                for jaw in (1,2):
                    placement = jaw_location(jaw,opening)
                    obstacles[f"carrier_{jaw}"] = placement*carriers[jaw]
                    for key,shape in local.items():
                        if jaw==side and key in ("finger","sensor",f"sensor_screw_{i}_M1p6x{spec.length:g}"):
                            continue  # Exact local checks handle these contacts.
                        obstacles[f"{key}_{jaw}"] = placement*shape
                summary = {"maximum_interference_mm3":0.0,"minimum_clearance_lower_bound_mm":float("inf")}
                for key,shape in {"screw_insertion":insertion,**tools}.items():
                    moving = location*shape
                    for obstacle,rigid in obstacles.items():
                        result = clearance(moving,rigid)
                        summary["maximum_interference_mm3"] = max(summary["maximum_interference_mm3"],result["interference_mm3"])
                        if result["clearance_mm"]<summary["minimum_clearance_lower_bound_mm"]:
                            summary["minimum_clearance_lower_bound_mm"] = result["clearance_mm"]
                            summary["limiting_pair"] = [key,obstacle]
                mechanism_checks[f"jaw{side}_opening{opening}"] = summary
        sensor_tool_checks = {key:clearance(shape,sensor) for key,shape in tools.items()}
        engagement = spec.length-(seat-P.sensor_rear_z)
        engagement_range = [length-(seat-P.sensor_rear_z)
                            for length in (spec.length_min,spec.length_max)]
        lip = pocket_lip_z(finger,x,y)
        reach = lip-(seat+S.head_height-S.driver_axial_engagement)
        assert abs(lip-seat-P.sensor_head_recess)<1e-6
        # Continuous material below the entire counterbore, including its
        # overhang into the electronics window (0.6 mm higher underside).
        floor_z = P.sensor_rear_z+P.sensor_boss_front_offset
        floor = cylinder(x,y,floor_z,P.sensor_head_pocket,seat-floor_z-P.sensor_seat_chamfer)
        floor -= cylinder(x,y,floor_z-.1,P.sensor_bore,seat-floor_z+.2)
        assert abs(floor.volume-volume_common(floor,finger))<1e-6
        tolerance_paths = {"insertion":clearance(insertion,tolerance_finger),
                           **{key:clearance(shape,tolerance_finger) for key,shape in tools.items()}}
        tolerance_blend = min(float(face.distance_to(tolerance_walls)) for face in screw.faces()
                              if BRepAdaptor_Surface(face.wrapped).GetType()==GeomAbs_Torus)
        assert max(r["interference_mm3"] for r in tolerance_paths.values())<1e-7
        assert tolerance_blend>0
        stack_range = [engagement_range[0]-P.sensor_print_stack_error,
                       engagement_range[1]+P.sensor_print_stack_error]
        assert 0<stack_range[0]<=stack_range[1]<S.tapped_depth_manual
        failures = [unexpected_sensor_overlap,seating_after,insertion_check["interference_mm3"],tool_vs_own_screw]
        failures += [r["interference_mm3"] for r in [*driver_checks.values(),*sensor_tool_checks.values()]]
        failures += [r["maximum_interference_mm3"] for r in mechanism_checks.values()]
        assert max(failures)<1e-7,(name,failures)
        assert 0<engagement_range[0]<=engagement_range[1]<S.tapped_depth_manual
        assert reach<S.driver_blade_length
        record = {"screw":name,"jaw_xy_mm":[x,y],"native_sensor_xy_mm":[x,P.sensor_y_translation-y],
            "selected_length_mm":spec.length,
            "reference_geometry_status":"PASS","actual_hardware_status":"UNVERIFIED",
            "overall_status":"UNVERIFIED","hole":measured_hole(x,P.sensor_y_translation-y),
            "seating":{"after_status":"PASS","after_overlap_mm3":seating_after,
                       "flat_seat_z_mm":seat,"relief_mm":P.sensor_seat_chamfer,
                       "counterbore_diameter_mm":P.sensor_head_pocket,"counterbore_depth_mm":lip-seat,
                       "counterbore_radial_rim_mm":(P.sensor_boss_diameter-P.sensor_head_pocket)/2,
                       "seat_to_sensor_stack_mm":seat-P.sensor_rear_z,
                       "minimum_floor_thickness_mm":seat-floor_z,
                       "minimum_supported_bearing_annulus_area_mm2":bearing.volume/.05},
            "insertion":{"status":"PASS","direction_jaw":[0,0,-1],"travel_mm":S.insertion_travel,
                         "sweep_vs_finger":insertion_check,"intentional_thread_envelope_overlap_mm3":raw_thread_overlap,
                         "unexpected_sensor_overlap_mm3":unexpected_sensor_overlap,
                         "method":"continuous axial outer sweep; maximum ISO knurled-head and screw-length envelopes",
                         "max_length_mm":spec.length_max},
            "clearance_mm":{**curved_clearance,"driver_shaft":driver_checks["shaft_sweep"]["clearance_mm"],
                            "minimum_free_surface":min(curved_clearance.values()),
                            "knurled_head_radial_sensitivity":(P.sensor_head_pocket-S.knurled_head_max)/2},
            "driver":{"status":"PASS for reference envelope","shaft_and_handle_checks":driver_checks,
                      "against_sensor":sensor_tool_checks,"nominal_hex_engagement_mm":S.driver_axial_engagement,
                      "socket_minimum_depth_mm":S.socket_depth_min,"socket_AF_clearance_per_flat_mm":(S.socket_af_min-S.driver_hex_af)/2,
                      "tool_vs_own_screw_overlap_mm3":tool_vs_own_screw,"highest_pocket_lip_z_mm":lip,
                      "required_slender_reach_mm":reach,"available_blade_length_mm":S.driver_blade_length,
                      "handle_axial_standoff_above_lip_mm":S.driver_blade_length-reach,
                      "actual_tip_transition_handle_and_torque_engagement":"UNVERIFIED"},
            "thread_engagement":{"geometric_depth_status":"PASS","functional_thread_strength_status":"UNVERIFIED",
                                 "nominal_penetration_mm":engagement,"length_tolerance_penetration_mm":engagement_range,
                                 "nominal_bottom_margin_mm":S.tapped_depth_manual-engagement,
                                 "max_length_bottom_margin_mm":S.tapped_depth_manual-engagement_range[1],
                                 "length_and_print_stack_penetration_mm":stack_range,
                                 "length_and_print_stack_bottom_margin_mm":S.tapped_depth_manual-stack_range[1],
                                 "fully_formed_thread_engagement_mm":None,
                                 "limit":"Printed error is an assumed bound only; actual seat/depth tolerances, tap lead, tip chamfer, preload and allowable torque unverified"},
            "PETG_sensitivity":{"status":"PASS for stated error envelope; physical capability UNVERIFIED",
                                "radial_hole_undersize_mm":P.sensor_print_radial_error,
                                "axial_stack_error_plus_minus_mm":P.sensor_print_stack_error,
                                "minimum_blend_clearance_mm":tolerance_blend,
                                "max_head_radial_clearance_mm":(tolerance_p.sensor_head_pocket-S.knurled_head_max)/2,
                                "shaft_radial_clearance_mm":(tolerance_p.sensor_bore-S.diameter)/2,
                                "path_checks":tolerance_paths},
            "complete_assembly_checks":mechanism_checks,"removal":"PASS for reverse path after unscrewing; finger remains attached"}
        records.append(record)
        print(f"Sensor {name}: reference paths PASS, actual hardware UNVERIFIED; "
              f"min free surface {record['clearance_mm']['minimum_free_surface']:.4f} mm, driver {record['clearance_mm']['driver_shaft']:.3f} mm",flush=True)
    report = {"status":"reference_geometry_passed_actual_hardware_unverified","units":"mm",
        "hardware":asdict(S),"physical_hardware_supplied":False,"full_print_release":False,
        "sensor_source_sha256":sha(SENSOR),"finger_volume_mm3":finger.volume,
        "prior_reinforced_volume_mm3":before.volume,
        "local_change":{"removed_mm3":float(removed.volume),"added_mm3":float(added.volume),
                        "removed_outside_six_pads_mm3":outside_removed,"added_outside_six_pads_mm3":outside_added,
                        "unchanged_web_mm":P.rib_thickness,"unchanged_skin_mm":P.arm_flange_thickness,
                        "unchanged_root_seat_mm":P.flange_thickness},
        "scope":"Six positions on each identical finger; attached moving blocks and complete standalone PiPER gripper; q=0/50/100",
        "continuous_access_argument":"All approach paths travel outward from their jaw. Same-jaw relative poses are fixed; opposing jaw distance increases with opening. Actuator Z bounds are independent of opening.",
        "clearance_definition":"Minimum free curved screw-surface distance to finger excluding the intended flat bearing planes; seat and mating-thread contact are intentional zero-clearance interfaces. Driver shaft clearance measured by B-rep distance.",
        "limits":["No physical screw or driver exists in the supplied assets; catalog references are not an approved BOM",
                  "Major-diameter thread envelope, not helical thread mating or torque analysis",
                  "Driver reduced-tip transition and handle diameter are not fully dimensioned; assumed handle diameter is explicitly recorded; Wera product page labels 97 mm as handle length, whereas PDF table ambiguously labels it overall length",
                  "Manual tapped depth and nominal penetration do not establish fully formed thread engagement or safe tightening torque",
                  "PETG radial/axial error cases are explicit sensitivity assumptions, not measured printer capabilities; coupon and real hardware remain necessary",
                  "Robot arm, surrounding workcell and human hand ergonomics are outside the supplied standalone gripper model"],
        "screws":records}
    if write:
        (V2/"docs/sensor-screw-access.json").write_text(json.dumps(report,indent=2)+"\n")
        write_report(report)
        draw_access(finger,sensor,screws)
    return report


def write_report(report):
    rows = []
    for r in report["screws"]:
        c = r["clearance_mm"];seat = r["seating"];t = r["thread_engagement"]
        rows.append(f"| {r['screw']} | {r['selected_length_mm']:g} | {seat['seat_to_sensor_stack_mm']:.1f} / {seat['minimum_floor_thickness_mm']:.1f} | PASS | PASS | PASS | UNVERIFIED | {c['minimum_free_surface']:.4f} / {c['driver_shaft']:.2f} | {t['length_and_print_stack_bottom_margin_mm']:.2f} |")
    change = report["local_change"]
    text = f"""# Six-screw M2324 assembly-access verification

All six positions **PASS the reference-hardware CAD checks** for insertion, seating, tightening and removal with the finger attached to the moving block. Actual hardware and PETG fit remain **UNVERIFIED**. No supplied screw or screwdriver specification exists beyond the sensor manufacturer's hole callout; catalog hardware is a parameterized design basis, not an approved physical BOM.

S1–S3 are jaw X=−8.75, distal to proximal; S4–S6 are X=+8.75 in the same order. Each finger uses two screws of each length; the complete pair uses four each.

| Screw | M1.6 length (mm) | Stack / minimum floor (mm) | Insert / seat | Tighten / remove | Geometric engagement | Actual hardware | Min free / driver clearance (mm) | Bottom margin incl. stated errors (mm) |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
"""+"\n".join(rows)+f"""

## Local geometry and retained structure

Each mounting pad is **Ø{P.sensor_boss_diameter:g}**, with a **Ø{P.sensor_head_pocket:g} × {P.sensor_head_recess:g} mm deep counterbore**, **1.5 mm radial rim**, and **Ø{P.sensor_bore:g} through bore**. The 0.15 × 45° bore-mouth relief opens to Ø2.4 and clears the under-head blend. Minimum ISO bearing annulus Ø2.72/Ø2.4 is fully supported: {report['screws'][0]['seating']['minimum_supported_bearing_annulus_area_mm2']:.3f} mm² per screw. Bearing contact intentionally has zero clearance; it is excluded from the free-surface minimum.

Local seat Z is **15.8 / 19.8 / 23.8 mm**; pad tops are **17.8 / 21.8 / 25.8 mm**. Seat-to-sensor stack is **6.6 / 10.6 / 14.6 mm**. Across the full counterbore footprint, the raised underside over the electronics window makes the minimum continuous floor **6.0 / 10.0 / 14.0 mm**. A wider shank passage and a shallow pocket replace the former deep head tunnels; no long narrow tool tunnel remains.

The **5 mm webs, 3.5 mm skins and 6 mm root seat** are unchanged. Exact boolean comparison against the [preserved prior reinforced V2](../revisions/before-shallow-counterbores/cad/exported/replacement_finger.step) finds **zero change outside the six Ø7.2 local zones**, and zero change in the root/arm region. Local material added is {change['added_mm3']:.3f} mm³ and removed is {change['removed_mm3']:.3f} mm³; net addition is {(change['added_mm3']-change['removed_mm3']):.3f} mm³. The sensor plane, 17.5 × 8 mm pattern, 70 mm functional reach, cable path and PiPER interfaces remain fixed. The earlier 47-file snapshot is also retained.

## Hardware basis

Catalog examples are Accu [M1.6×8]({S.screw_8_source}), [M1.6×12]({S.screw_12_source}) and [M1.6×16]({S.screw_source}), all socket caps with **Ø3 × 1.6 mm heads, 1.5 mm hex drives and 0.35 mm pitch**. The [NBK ISO 4762/JIS table]({S.dimensions_source}) supplies conservative dimensional bounds: knurled-head maximum Ø3.14, under-head blend R0.2, minimum bearing Ø2.72, socket AF1.52 and depth0.7. Length bounds used are 7.71–8.29, 11.65–12.35 and 15.65–16.35 mm. Exact purchased lengths, finishes and head styles remain unconfirmed. The CAD models include heads, hex sockets and blends; threads use their Ø1.6 major-diameter envelope, without an invented mating helix.

The manufacturer specifies **six M1.6 tapped holes, 2 mm thread depth**, with 17.5 mm horizontal and 8 mm vertical pitch (supplied manual PDF p.8 and user confirmation). All six STEP holes contain Ø1.25 minor cylinders, 2 mm long; they are not clearance holes. Fully formed thread depth, tap lead and tightening torque cannot be established from smooth CAD pilots.

## Driver access and PETG allowances

The reference [Wera 2054 Micro 05118066001]({S.driver_source}) has a 1.5 mm hex, **Ø3 mm shaft and 60 mm blade**. Nominal engaged length is **0.7 mm**. Only **1.1 mm** of slender reach is needed below each pad top, leaving **58.9 mm** before the modeled handle begins. The [product page]({S.driver_product_source}) calls 97 mm the handle length; the ambiguous PDF label is resolved conservatively to that longer interpretation. Handle diameter remains an explicit **assumed Ø20 mm**; its full envelope is checked. Actual tip transition/chamfer and torque-bearing engagement remain unverified.

Nominal radial clearance is **0.60 mm for the driver/plain head**, **0.53 mm for a Ø3.14 knurled head**, and **0.25 mm for the screw shank**. The minimum free screw-surface clearance is **{min(r['clearance_mm']['minimum_free_surface'] for r in report['screws']):.4f} mm**, at the relieved under-head blend. This replaces the former 0.10 mm driver gap.

A uniform **0.15 mm radial hole undersize** (0.30 mm on diameter) sensitivity is checked by rebuilding the finger with Ø1.8 bores and Ø3.9 counterbores. All six insertion and tool sweeps still clear: driver **0.45 mm**, maximum head **0.38 mm**, shank **0.10 mm** radial; blend minimum **{min(r['PETG_sensitivity']['minimum_blend_clearance_mm'] for r in report['screws']):.4f} mm**. This error envelope is a design check, not a measured PETG capability. Hole position, ovality, support residue and real layer quality still need the existing fit check. The updated coupon reproduces the 2 mm pocket and relief in the existing 5.5 mm coupon body; it does not reproduce all three long shank stacks.

## Engagement and complete assembly checks

All lengths give **1.4 mm nominal penetration**, leaving **0.6 mm** to the manufacturer's nominal 2 mm depth. ISO screw-length tolerance alone leaves at least **0.31 / 0.25 / 0.25 mm**. Combining it with an explicit **±0.15 mm printed stack error** gives penetration **0.96–1.84 / 0.90–1.90 / 0.90–1.90 mm**, leaving **0.16 / 0.10 / 0.10 mm** respectively. Sensor depth tolerance, tap lead and screw-tip shape are unknown; therefore usable full-thread engagement, strength and actual non-bottoming remain physical checks. Measure protrusion before assembly; keep lengths assigned to their rows and do not substitute a longer screw.

Continuous 30 mm axial insertion/removal sweeps include the maximum screw length and Ø3.14 head rotation envelope. The only exempt housing overlap is the matching coaxial Ø1.6 volume within the documented threaded depth. Tightening uses the engaged hex plus shaft; the driver socket fit is checked separately. Checks include both attached fingers, the full sensor housing, actual retained blocks, other installed screws, opposite jaw, plug, leads, tie and service loops at q=0/50/100. The entire actuator mesh is bounded conservatively to prove separation. Same-jaw poses are fixed, the paths point outward, opposite-jaw separation increases with opening, and actuator axial separation is constant. The robot arm, workcell and hand ergonomics are outside the supplied standalone gripper model.

[Machine results](sensor-screw-access.json) · [six access paths](../drawings/sensor_screw_access.png) · [counterbore section](../drawings/sensor_screw_seating.png) · [complete assembly/tool view](../drawings/sensor_screw_access_assembly.png) · [interactive complete CAD](../cad/exported/sensor_screw_access.glb) · [local STEP study](../cad/exported/sensor_screw_access.step). All dimensions are mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
"""
    (V2/"docs/sensor-screw-access.md").write_text(text)


def draw_access(finger,sensor,screws):
    from build_v2 import BLUE,GREEN,STEEL,AMBER,assembly_meshes,local_meshes,export_scene
    from render import render
    purple = (155,82,189,255)
    close = {"finger_section":cad_mesh(finger & box_between(-15,15,-26,4,3,40),BLUE),
             "sensor":cad_mesh(sensor,GREEN)}
    children = []
    for i,(x,y) in enumerate(P.sensor_axes,1):
        screw = sensor_screw(x,y)
        close[f"S{i}_seated"] = cad_mesh(screw,STEEL)
        close[f"S{i}_inserted_pose"] = cad_mesh(Pos(0,0,30)*screw,AMBER)
        close[f"S{i}_axis"] = cad_mesh(cylinder(x,y,P.sensor_screw_seat_z(y),.25,32),AMBER)
        # Show the engaged shaft locally; full 60 mm shaft/handle in assembly.
        tool = driver_components(x,y)
        local_tool = tool["engaged_hex_tip"]+tool["shaft"]
        local_tool &= box_between(x-2,x+2,y-2,y+2,P.sensor_screw_seat_z(y),P.sensor_boss_top_z(y)+4)
        close[f"S{i}_driver"] = cad_mesh(local_tool,purple)
        for name,shape in ((f"S{i}_screw",screw),(f"S{i}_continuous_insertion",screw_insertion_sweep(x,y)),
                           (f"S{i}_reference_driver",tool["engaged_hex_tip"]+tool["shaft"]+tool["assumed_handle"])):
            shape.label=name;children.append(shape)
    labels = [((x,y,P.sensor_screw_seat_z(y)+31.6),f"S{i}",(-25,-30)) for i,(x,y) in enumerate(P.sensor_axes,1)]
    render(close,V2/"drawings/sensor_screw_access.png",(1.25,-1.4,1.3),
           "Six sensor screws / straight insertion and driver paths",
           "Amber: insertion pose + axis   Steel: seated   Purple: engaged tool segment; one screw at a time",labels,
           up_axis=(0,1,0))
    x,y = P.sensor_axes[2]
    clip = box_between(x-4.8,x+4.8,y,y+3.6,6,30.2)
    section = {"finger_section":cad_mesh(finger&clip,BLUE),"sensor_section":cad_mesh(sensor&clip,GREEN),
               "screw_section":cad_mesh(sensor_screw(x,y)&clip,STEEL)}
    tool = driver_components(x,y)
    section["driver_section"] = cad_mesh((tool["engaged_hex_tip"]+tool["shaft"])&clip,purple)
    render(section,V2/"drawings/sensor_screw_seating.png",(0,-1,0),
           "S3 axial section / shallow counterbore / reinforced material retained",
           "Blue: printed PETG   Green: sensor   Steel: M1.6 x 16 reference   Purple: 1.5 mm hex driver",
           labels=[((x+1.95,y,24.8),"Counterbore: diameter 4.2 x 2.0 deep",(175,-45)),
                   ((x,y,28.5),"Diameter 3 driver; 0.60 radial gap",(180,0)),
                   ((x-1.4,y,24.6),"Head: diameter 3 x 1.6 high",(-445,-75)),
                   ((x+1.1,y,23.8),"Flat seat Z=23.8 / 0.15 relief",(180,55)),
                   ((x+2.8,y,16),"Minimum PETG floor: 14.0 mm",(145,0)),
                   ((x-1.7,y,9.2),"Sensor mounting face Z=9.2",(-420,-35)),
                   ((x,y,7.8),"Penetration 1.4 / depth margin 0.6",(175,35))])
    assembly = assembly_meshes(local_meshes(finger,sensor),50)
    location = jaw_location(1,50)
    tool_shape = tool["engaged_hex_tip"]+tool["shaft"]+tool["assumed_handle"]
    assembly["S3_driver_reference_with_assumed_handle"] = cad_mesh(location*tool_shape,purple)
    for i,(x,y) in enumerate(P.sensor_axes,1):
        assembly[f"S{i}_access_axis"] = cad_mesh(location*cylinder(x,y,P.sensor_screw_seat_z(y),.3,32),AMBER)
    export_scene(assembly,V2/"cad/exported/sensor_screw_access.glb")
    render(assembly,V2/"drawings/sensor_screw_access_assembly.png",(1.3,-1.6,.8),
           "Attached finger / full PiPER gripper / reference driver",
           "50 mm command shown; both jaws checked at 0 / 50 / 100. Purple handle is an assumed bounding envelope.")
    for name,shape in (("reinforced_finger",finger),("M2324",sensor),
                       ("retained_moving_block",faceted_solid(carrier_and_finger(1)[0]))):
        shape = Pos(0,0,0)*shape;shape.label=name;children.append(shape)
    export_step(Compound(children=children,label="Local screw access alternatives; complete actuator in GLB"),
                V2/"cad/exported/sensor_screw_access.step")


if __name__=="__main__":
    verify_sensor_access(write=True)
