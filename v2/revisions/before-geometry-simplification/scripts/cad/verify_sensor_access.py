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
                                make_finger, placed_sensor, plug_envelope, service_cable, strain_relief_band, sensor_access_pocket)
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
                and abs(cyl.Radius()-P.sensor_access_width/2)<1e-5
                and abs(cyl.Axis().Direction().Z())>.999):
                ends.append(face.bounding_box().max.Z)
    assert ends
    return max(ends)


def verify_sensor_access(finger=None,sensor=None,write=False):
    finger = make_finger() if finger is None else finger
    sensor = placed_sensor() if sensor is None else sensor
    archive = json.loads((V2/"docs/pre-short-pad-revision.json").read_text())
    before = import_step(V2/archive["snapshot"]/"cad/exported/replacement_finger.step")
    # Isolate the earlier sensor-interface alteration from the later measured
    # 0.074 mm core-roof correction. Check both, against their actual old solids.
    pad_archive = json.loads((V2/"docs/pre-printability-revision.json").read_text())
    pad_revision = import_step(V2/pad_archive["snapshot"]/"cad/exported/replacement_finger.step")
    from verify_printability import check_skin_correction
    skin_correction = check_skin_correction(finger)
    # Changes must stay inside the sensor fastener zones: old round towers,
    # new short pads and U pockets. Root/arm and outer rails are protected.
    zones = Compound(children=[box_between(x-3.601,x+3.601,y-3.601,y+3.601,
                                          P.sensor_rear_z-1,P.root_top_z+2)
                               for x,y in P.sensor_axes])
    removed,added = before-pad_revision,pad_revision-before
    outside_removed = volume_common(removed,before-zones)
    outside_added = volume_common(added,pad_revision-zones)
    assert max(outside_removed,outside_added)<1e-6
    protected = box_between(-15,15,P.mount_y-1,P.sensor_frame_proximal_y,0,40)
    assert volume_common(removed,protected)+volume_common(added,protected)<1e-6
    outer_rails = Compound(children=[box_between(a,b,-24.5,P.tip_y,0,40)
                                      for a,b in ((-14,-11.001),(11.001,14))])
    # Protect the original sloping rail, not the rejected tower material that
    # projected above it. Compare with the preserved reinforcement before towers.
    structural_archive = json.loads((V2/"docs/pre-counterbore-revision.json").read_text())
    structural_reference = import_step(V2/structural_archive["snapshot"]/"cad/exported/replacement_finger.step")
    rail_before,rail_after = structural_reference&outer_rails,finger&outer_rails
    rail_change = (rail_before-rail_after).volume+(rail_after-rail_before).volume
    assert rail_change<1e-6
    # A uniform radial undersize sensitivity, not an asserted printer accuracy.
    tolerance_p = replace(P,sensor_bore=P.sensor_bore-2*P.sensor_print_radial_error,
                           sensor_access_width=P.sensor_access_width-2*P.sensor_print_radial_error)
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
        assert abs(seat-P.sensor_rear_z-P.sensor_pad_thickness)<1e-8
        assert 2.5 <= seat-P.sensor_rear_z <= 4.0
        # A head-width lateral corridor opens continuously to the central
        # sensor window. No fully enclosed tool tunnel remains above the pad.
        mouth = box_between(min(0,x),max(0,x),y-S.knurled_head_max/2,
                            y+S.knurled_head_max/2,seat+.001,P.root_top_z+1)
        mouth_overlap = volume_common(mouth,finger)
        assert mouth_overlap<1e-7
        # Continuous short flange under the head and access-pocket floor.
        floor_z = P.sensor_rear_z+P.sensor_pad_front_offset
        floor = cylinder(x,y,floor_z,P.sensor_access_width,seat-floor_z-P.sensor_seat_chamfer)
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
                       "head_seat_type":"flat short flange, open U pocket; no counterbore",
                       "open_access_width_mm":P.sensor_access_width,
                       "lateral_mouth_overlap_mm3":mouth_overlap,
                       "minimum_hole_edge_ligament_mm":(min(P.sensor_pad_width,P.sensor_pad_length)-P.sensor_bore)/2,
                       "outer_rail_width_mm":P.width/2-abs(x)-P.sensor_access_width/2,
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
                            "knurled_head_radial_sensitivity":(P.sensor_access_width-S.knurled_head_max)/2},
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
                                "max_head_radial_clearance_mm":(tolerance_p.sensor_access_width-S.knurled_head_max)/2,
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
        "printability_skin_correction":skin_correction,
        "local_change":{"removed_mm3":float(removed.volume),"added_mm3":float(added.volume),
                        "removed_outside_six_pads_mm3":outside_removed,"added_outside_six_pads_mm3":outside_added,
                        "unchanged_web_mm":P.rib_thickness,"unchanged_skin_mm":P.arm_flange_thickness,
                        "unchanged_root_seat_mm":P.flange_thickness,
                        "unchanged_outer_rail_width_mm":3.0,
                        "outer_rail_difference_mm3":rail_change,
                        "old_seat_to_sensor_stack_mm":[6.6,10.6,14.6],
                        "new_seat_to_sensor_stack_mm":P.sensor_pad_thickness},
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
        c = r["clearance_mm"];seat = r["seating"];d = r["driver"]
        rows.append(f"| {r['screw']} | {r['selected_length_mm']:g} | {seat['seat_to_sensor_stack_mm']:.1f} | PASS | PASS | PASS | UNVERIFIED | {c['minimum_free_surface']:.4f} / {c['driver_shaft']:.2f} | {d['required_slender_reach_mm']:.3f} |")
    change = report["local_change"]
    text = f"""# M2324 short mounting pads and open screw access

**Every head seat is now Z=12.8, only 3.6 mm behind the unchanged sensor plane Z=9.2.** The old 6.6 / 10.6 / 14.6 mm passages and six cylindrical towers are removed. All six positions use the same candidate **M1.6×5** screw. No counterbore depth is being substituted for the actual pass-through thickness.

All six positions pass reference-hardware CAD insertion, seating, tightening and removal checks with the finger attached. Actual hardware, printed fit and usable full thread engagement remain **UNVERIFIED**. S1–S3 are X=−8.75 from distal to proximal; S4–S6 are X=+8.75 in the same order. There are six screws per finger, twelve for the two-finger assembly.

| Screw | M1.6 length (mm) | Actual seat-to-sensor stack (mm) | Insert / seat | Tighten / remove | Open side access | Actual hardware | Min free / driver clearance (mm) | Blade reach beside adjacent wall (mm) |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
"""+"\n".join(rows)+f"""

## Local mounting geometry

Six short **6 × 6 mm rounded flanges** support the heads. All seats are flat at Z=12.8, giving **3.6 mm pass-through** over the sensor mounting strips. The small lips added toward the electronics window start at Z=9.8, so their minimum thickness is **3.0 mm** and they do not contact the electronics. Ø2.1 clearance bores retain a 0.15 × 45° mouth relief (Ø2.4 mouth). Minimum bore-to-pad-edge ligament is **1.95 mm**; nominal head-to-pad-edge distance is **1.50 mm**. The minimum ISO Ø2.72/Ø2.4 bearing annulus is fully supported, area **{report['screws'][0]['seating']['minimum_supported_bearing_annulus_area_mm2']:.3f} mm²**.

**4.5 mm wide U pockets** open from each seat into the existing central sensor window. They extend through the local sloping material above the pads and have **R0.4 floor transitions**. The outer rail stays continuous at **3 mm wide**, with **3.5 mm longitudinal ligaments between adjacent pocket openings**. The head sits directly on the flange; there is no enclosing counterbore or long cylindrical tool tunnel. The head-width lateral corridor is checked for zero material overlap from each seat up to open space. Adjacent reinforcing walls remain tall; their height is reported as blade reach, not as screw pass-through thickness.

The sensor-interface alteration preserves the **5 mm main webs, root collar and 6 mm root seat**. Exact boolean comparison of the preserved short-pad and long-passage solids finds zero change outside the six mounting zones. The current part also incorporates the separately checked printability correction: moving the inner core roof down **0.074 mm** makes the sloped rear skin **3.5 mm perpendicular to its surface**, instead of 3.428 mm. That correction adds **{report['printability_skin_correction']['added_mm3']:.3f} mm³** only at the core roof; no material is removed and no sensor/root interface moves. The original outer 3 mm rails still match the preserved reinforcement. Sensor-zone material removed is **{change['removed_mm3']:.3f} mm³**, added **{change['added_mm3']:.3f} mm³**. The actual part is **one valid connected solid**; no removable plate or extra joint is needed. Local pad strength and torque capacity remain physically unverified.

## Screw and driver basis

[NBK SNS/SNSS-M1.6-5]({S.screw_source}) documents a standard **5 mm** screw with **0.35 pitch, Ø3 × 1.6 head and 1.5 mm hex drive**. The [ISO/JIS extract]({S.dimensions_source}) supplies length bounds **4.76–5.24 mm**, maximum knurled head Ø3.14, under-head blend R0.2, minimum bearing Ø2.72, socket AF1.52 and minimum depth 0.7. These are parameterized reference dimensions, not measurements of supplied screws. The CAD includes the head, socket and blend; threads use their major-diameter envelope.

The manufacturer's six **M1.6 tapped holes, 2 mm depth**, 17.5 mm horizontal and 8 mm vertical pitch remain authoritative. Every vendor STEP axis is remeasured; its Ø1.25 minor cylinder is not treated as a clearance hole. Sensor location and orientation are unchanged.

The reference [Wera 2054 Micro 05118066001]({S.driver_source}) has a **1.5 mm hex, Ø3 mm shaft and 60 mm blade**, modeled with 0.7 mm axial engagement. Its [product table]({S.driver_product_source}) gives 97 mm handle length; the handle diameter is an explicit assumed Ø20 mm envelope. Actual tip transition, handle and torque-bearing socket engagement remain unverified. Each tool pose is an alternative, one screw at a time.

## PETG allowance and thread depth

Nominal driver clearance to the pocket walls is **0.75 mm radial**. Minimum free screw-to-finger clearance is **{min(r['clearance_mm']['minimum_free_surface'] for r in report['screws']):.4f} mm** at the under-head blend; deliberate flat-seat and thread contact are excluded. With a uniform **0.15 mm radial hole/pocket undersize** case, Ø1.8 bores and 4.2 mm pockets still pass every screw and tool sweep. Driver clearance is then **0.60 mm**, shank clearance 0.10, and minimum blend clearance **{min(r['PETG_sensitivity']['minimum_blend_clearance_mm'] for r in report['screws']):.4f} mm**. These are stated error assumptions, not measured printer capability. Position error, ovality and support residue remain physical checks. The existing coupon now reproduces the **3.6 mm pass-through thickness** and bore-mouth relief.

All six screws penetrate **5 − 3.6 = 1.4 mm nominally**, leaving **0.6 mm** to the manufacturer's 2 mm depth. Screw-length tolerance gives **1.16–1.64 mm** penetration. Including an assumed **±0.15 mm printed-stack error** gives **1.01–1.79 mm**, leaving **0.21 mm minimum nominal-depth margin**. Tap lead, fully formed thread depth, screw-tip shape, actual sensor depth tolerance and permissible torque are unknown. Check actual protrusion before assembly; a 6 mm screw is not a substitute in this 3.6 mm stack.

## Complete assembly verification

Continuous 30 mm axial insertion/removal sweeps include the maximum screw length and Ø3.14 head rotation envelope. Only the matching Ø1.6 shaft volume within the documented 2 mm tap depth is exempted as intended thread contact. The audit includes both attached fingers, sensor housings, original moving blocks, other installed screws, plug, leads, tie, service loops and the conservative bounding envelope of the complete original actuator at commands 0/50/100. Same-jaw poses remain fixed, opposing-jaw separation increases with opening, and actuator axial separation is constant. The robot arm, surrounding workcell and hands are outside the supplied standalone model.

[Old/new cross-section at the same scale](../drawings/sensor_screw_seating.png) · [six open access paths](../drawings/sensor_screw_access.png) · [complete driver/assembly view](../drawings/sensor_screw_access_assembly.png) · [interactive CAD](../cad/exported/sensor_screw_access.glb) · [access STEP](../cad/exported/sensor_screw_access.step) · [machine results](sensor-screw-access.json). Units are mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
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
        local_tool &= box_between(x-2,x+2,y-2,y+2,P.sensor_screw_seat_z(y),P.sensor_screw_seat_z(y)+12)
        if i==3:
            close[f"S{i}_driver"] = cad_mesh(local_tool,purple)
        for name,shape in ((f"S{i}_screw",screw),(f"S{i}_continuous_insertion",screw_insertion_sweep(x,y)),
                           (f"S{i}_reference_driver",tool["engaged_hex_tip"]+tool["shaft"]+tool["assumed_handle"])):
            shape.label=name;children.append(shape)
    labels = [((x,y,P.sensor_screw_seat_z(y)+31.6),f"S{i}",(-25,-30)) for i,(x,y) in enumerate(P.sensor_axes,1)]
    render(close,V2/"drawings/sensor_screw_access.png",(.45,-1,1.8),
           "Six short mounting pads / open U pockets / straight screw paths",
           "Amber: insertion pose + axis   Steel: seated M1.6 x 5   Purple: example S3 driver",labels,
           up_axis=(0,1,0))
    x,y = P.sensor_axes[2]
    # Compare real archived and current S3 B-reps at the same scale and datum.
    archive = json.loads((V2/"docs/pre-short-pad-revision.json").read_text())
    previous_access = import_step(V2/archive["snapshot"]/"cad/exported/sensor_screw_access.step")
    old = {part.label:part for part in previous_access.children}
    # A thin section suppresses unrelated far-side ribs in the orthographic
    # view, so the open side of the pocket is shown without projected walls.
    clip = box_between(x-5.25,x+5.25,y,y+.05,6,29)
    section = {}
    tool = driver_components(x,y)
    tool_shape = tool["engaged_hex_tip"]+tool["shaft"]
    for name,shape,color,offset in (
            ("old_finger",old["reinforced_finger"],BLUE,-9-x),
            ("old_sensor",sensor,GREEN,-9-x),
            ("old_screw",old["S3_screw"],STEEL,-9-x),
            ("old_driver",old["S3_reference_driver"],purple,-9-x),
            ("new_finger",finger,BLUE,9-x),
            ("new_sensor",sensor,GREEN,9-x),
            ("new_screw",sensor_screw(x,y),STEEL,9-x),
            ("new_driver",tool_shape,purple,9-x)):
        section[name] = cad_mesh(Pos(offset,0,0)*(shape&clip),color)
    section["unchanged_sensor_plane"] = cad_mesh(box_between(-15,15,y-.04,y-.02,9.18,9.22),(190,65,65,255))
    section_path = V2/"drawings/sensor_screw_seating.png"
    render(section,section_path,(0,-1,0),
           "S3 section comparison / actual screw passage: 14.6 to 3.6 mm",
           "Same scale. Blue: PETG   Green: sensor   Steel: screw   Purple: driver   Red: unchanged Z=9.2 plane",
           labels=[((-10.4,y,24.6),"OLD: M1.6 x 16",(-200,-80)),
                   ((-10.3,y,23.8),"Seat Z=23.8",(-200,15)),
                   ((10.3,y,13.6),"NEW: M1.6 x 5",(70,-60)),
                   ((7.5,y,12.8),"Seat Z=12.8",(-90,65)),
                   ((11.0,y,19.4),"Open toward sensor window",(-45,-15))])
    # Dimension arrows use the same orthographic projection as render().
    from PIL import Image, ImageDraw
    from render import font
    im = Image.open(section_path);draw = ImageDraw.Draw(im)
    points = np.vstack([m.vertices for m in section.values()])[:,[0,2]]
    center = (points.min(0)+points.max(0))/2
    span = np.ptp(points,axis=0)
    scale = min(1220/span[0],850/span[1])
    def xy(xx,zz):
        return (720+(xx-center[0])*scale,555-(zz-center[1])*scale)
    for axis,dim_x,top,text in ((-9,-3.5,23.8,"14.6 mm"),(9,14.5,12.8,"3.6 mm")):
        u,v0 = xy(dim_x,9.2);_,v1 = xy(dim_x,top)
        draw.line((u,v0,u,v1),fill="#172d45",width=2)
        for level,v,direction in ((9.2,v0,-1),(top,v1,1)):
            start,_ = xy(axis,level)
            draw.line((start,v,u+7,v),fill="#526477",width=1)
            draw.polygon([(u,v),(u-5,v+direction*9),(u+5,v+direction*9)],fill="#172d45")
        tx,ty = u+9,(v0+v1)/2-12
        box = draw.textbbox((tx,ty),text,font=font(21))
        draw.rectangle((box[0]-4,box[1]-3,box[2]+4,box[3]+3),fill="#f5f7fa")
        draw.text((tx,ty),text,font=font(21),fill="#172d45")
    im.save(section_path)
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
