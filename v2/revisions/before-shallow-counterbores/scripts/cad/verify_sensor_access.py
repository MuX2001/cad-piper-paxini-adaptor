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
from build123d import Color, Compound, Pos, export_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Torus

from references import (SENSOR, cad_mesh, carrier_and_finger, faceted_solid,
                        sensor_native, vendor_mesh)
from replacement_finger import (P, bore, box_between, cable_envelope, hardware, jaw_location,
                                make_finger, placed_sensor, plug_envelope, service_cable, strain_relief_band)
from sensor_fasteners import (S, cylinder, driver_components, driver_sweeps, sensor_screw,
                              screw_insertion_sweep)


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
                and abs(surface.Plane().Location().Z()-P.sensor_screw_seat_z)<1e-8)
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
    before = make_finger(replace(P,sensor_seat_chamfer=0))
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
        screw = sensor_screw(x,y)
        insertion = screw_insertion_sweep(x,y)
        tools = driver_sweeps(x,y)
        components = driver_components(x,y)
        assert P.sensor_screw_seat_z-S.length_max+S.insertion_travel > finger.bounding_box().max.Z
        # Exempt ONLY the coaxial major-diameter volume inside the documented
        # tapped depth. A helix-free vendor pilot is not a clearance hole.
        intended_thread = cylinder(x,y,P.sensor_rear_z-S.tapped_depth_manual,
                                   S.diameter+2e-6,S.tapped_depth_manual+1e-6)
        sensor_outside_thread = sensor-intended_thread
        raw_thread_overlap = volume_common(insertion,sensor)
        unexpected_sensor_overlap = volume_common(insertion,sensor_outside_thread)
        insertion_check = clearance(insertion,finger)
        driver_checks = {key:clearance(shape,finger) for key,shape in tools.items()}
        seating_before = volume_common(screw,before)
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
        bearing = cylinder(x,y,P.sensor_screw_seat_z-.05,S.bearing_diameter_min,.05)
        bearing -= cylinder(x,y,P.sensor_screw_seat_z-.1,
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
                        if jaw==side and key in ("finger","sensor",f"sensor_screw_{i}_M1p6x4"):
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
        engagement = S.length-(P.sensor_screw_seat_z-P.sensor_rear_z)
        engagement_range = [length-(P.sensor_screw_seat_z-P.sensor_rear_z)
                            for length in (S.length_min,S.length_max)]
        lip = pocket_lip_z(finger,x,y)
        reach = lip-(P.sensor_screw_seat_z+S.head_height-S.driver_axial_engagement)
        failures = [unexpected_sensor_overlap,seating_after,insertion_check["interference_mm3"],tool_vs_own_screw]
        failures += [r["interference_mm3"] for r in [*driver_checks.values(),*sensor_tool_checks.values()]]
        failures += [r["maximum_interference_mm3"] for r in mechanism_checks.values()]
        assert max(failures)<1e-7,(name,failures)
        assert 0<engagement_range[0]<=engagement_range[1]<S.tapped_depth_manual
        assert reach<S.driver_blade_length
        record = {"screw":name,"jaw_xy_mm":[x,y],"native_sensor_xy_mm":[x,P.sensor_y_translation-y],
            "reference_geometry_status":"PASS","actual_hardware_status":"UNVERIFIED",
            "overall_status":"UNVERIFIED","hole":measured_hole(x,P.sensor_y_translation-y),
            "seating":{"before_status":"FAIL","before_overlap_mm3":seating_before,
                       "after_status":"PASS","after_overlap_mm3":seating_after,
                       "flat_seat_z_mm":P.sensor_screw_seat_z,"relief_mm":P.sensor_seat_chamfer,
                       "minimum_supported_bearing_annulus_area_mm2":bearing.volume/.05},
            "insertion":{"status":"PASS","direction_jaw":[0,0,-1],"travel_mm":S.insertion_travel,
                         "sweep_vs_finger":insertion_check,"intentional_thread_envelope_overlap_mm3":raw_thread_overlap,
                         "unexpected_sensor_overlap_mm3":unexpected_sensor_overlap,
                         "method":"continuous axial outer sweep; head rotation enclosed by cylinder; 4.24 mm max screw length"},
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
                                 "fully_formed_thread_engagement_mm":None,
                                 "limit":"Excludes unknown printed seat tolerance, tap lead, tip chamfer, preload and allowable torque"},
            "complete_assembly_checks":mechanism_checks,"removal":"PASS for reverse path after unscrewing; finger remains attached"}
        records.append(record)
        print(f"Sensor {name}: reference paths PASS, actual hardware UNVERIFIED; "
              f"min free surface {record['clearance_mm']['minimum_free_surface']:.4f} mm, shaft 0.100 mm",flush=True)
    report = {"status":"reference_geometry_passed_actual_hardware_unverified","units":"mm",
        "hardware":asdict(S),"physical_hardware_supplied":False,"full_print_release":False,
        "sensor_source_sha256":sha(SENSOR),"finger_volume_mm3":finger.volume,
        "before_seat_relief_volume_mm3":before.volume,"material_removed_mm3":before.volume-finger.volume,
        "scope":"Six positions on each identical finger; attached moving blocks and complete standalone PiPER gripper; q=0/50/100",
        "continuous_access_argument":"All approach paths travel outward from their jaw. Same-jaw relative poses are fixed; opposing jaw distance increases with opening. Actuator Z bounds are independent of opening.",
        "clearance_definition":"Minimum free curved screw-surface distance to finger excluding the intended flat bearing planes; seat and mating-thread contact are intentional zero-clearance interfaces. Driver shaft clearance measured by B-rep distance.",
        "limits":["No physical screw or driver exists in the supplied assets; catalog references are not an approved BOM",
                  "Major-diameter thread envelope, not helical thread mating or torque analysis",
                  "Driver reduced-tip transition and handle diameter are not fully dimensioned; assumed handle diameter is explicitly recorded; Wera product page labels 97 mm as handle length, whereas PDF table ambiguously labels it overall length",
                  "Manual tapped depth and nominal penetration do not establish fully formed thread engagement or safe tightening torque",
                  "Nominal CAD clearance is not a measured PETG print tolerance; particularly the 0.035 mm blend clearance and 0.03 mm knurled-head sensitivity",
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
        x,y = r["jaw_xy_mm"];c = r["clearance_mm"];d = r["driver"]
        rows.append(f"| {r['screw']} | {x:.2f}, {y:.3f} | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | {c['minimum_free_surface']:.4f} / {c['head_wall']:.3f} / {c['driver_shaft']:.3f} | {d['required_slender_reach_mm']:.3f} |")
    text = """# Six-screw M2324 assembly-access verification

All six locations pass the **documented reference-hardware geometry check after a local seating correction**. Actual screw/tool selection and physical fit remain **UNVERIFIED**: the user confirmed that no additional hardware specification is available. This is not a print release. IDs S1–S3 are jaw X=−8.75 from distal to proximal; S4–S6 are X=+8.75 in the same order. Both complete jaw assemblies are checked.

| Screw | Jaw X, Y (mm) | Axial insertion | Driver / removal path | Geometric depth / usable thread | Overall actual hardware | Min free / head radial / driver radial clearance (mm) | Required slender reach (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- |
"""+"\n".join(rows)+f"""

The minimum free clearance is **0.0354 mm at the maximum under-head blend**, excluding intentional flat-seat and thread contact. Plain head and shaft paths have 0.100 mm radial clearance. A generic ISO knurled head can reach Ø3.14 and would leave only 0.030 mm radial clearance in the existing Ø3.2 pocket; it is not interchangeable with the checked plain Ø3.0 head without confirming fit. No PETG tolerance is inferred from these nominal CAD values.

## Hardware basis and seating correction

The supplied PaXini manual (PDF p.8, printed p.5) calls out six **M1.6 tapped holes, depth 2 mm**. All six source STEP holes have Ø1.25 minor cylinders, native Z=−2.05…−0.05, consistent with tap pilots rather than clearance holes. The STEP has no thread helix. A physical thread gauge, usable full-flank depth and permissible tightening torque are unavailable.

The reference is a **plain-head M1.6×4, pitch 0.35 mm** socket screw; [NBK SNS/SNSS-M1.6-4]({S.screw_source}) documents the main dimensions. The [NBK ISO 4762/JIS dimensional table]({S.dimensions_source}) supplies the conservative bounds: head Ø3.0 × 1.6, minimum hex socket AF1.52/depth0.7, maximum under-head diameter2.0 and radius0.2, minimum bearing diameter2.72, and length3.76…4.24. The authored CAD includes the head, actual hex recess and maximum under-head blend. The threaded portion is a conservative Ø1.6 major-diameter envelope; detailed helical mating is unverified. No supplier screw file is claimed.

Before correction each maximum-radius blend overlapped the sharp printed seat edge by **0.005042 mm³**. Six **0.15 × 45° bore-mouth chamfers**, also reproduced in the fit coupon, remove that overlap. The seat stays at Z=11.8, the head pocket stays Ø3.2, and the finger's webs, skins, sensor datum and reach are unchanged. Total material removed is **{report['material_removed_mm3']:.4f} mm³**. The guaranteed Ø2.72/Ø2.10 flat bearing annulus remains fully supported; its area is {report['screws'][0]['seating']['minimum_supported_bearing_annulus_area_mm2']:.3f} mm² per screw. Nominal zero gap at the flat seat is intended.

## Insertion, tightening and removal

Screws approach along jaw −Z from 30 mm outside the seated position, after the replacement finger is bolted to the moving block and the sensor is seated. Continuous swept volumes enclose both screw rotation and translation, including the maximum 4.24 mm length. The only exempt sensor contact is the matching coaxial Ø1.6 volume inside the documented 2 mm tapped depth. No housing/head interference is hidden by a blanket exemption.

The reference driver is [Wera 2054 Micro 05118066001]({S.driver_source}): 1.5 mm hex, Ø3 mm shaft and 60 mm blade. A 0.7 mm engaged hex tip fits the minimum socket. The full shaft begins immediately above the head as a conservative bound. Its required slender reach varies with the sloped pocket lip as tabulated; the remaining blade extends beyond the lip before the handle begins. The [manufacturer's product page]({S.driver_product_source}) labels 97 mm as handle length, while the PDF table ambiguously labels it overall length. The longer interpretation is used. Handle diameter is not dimensioned here, so an explicitly **assumed Ø20 × 97 mm handle envelope** is checked. The actual reduced-tip transition, tip chamfer, handle and torque-bearing engagement remain UNVERIFIED. These tool positions are alternatives, one screw at a time.

The checks include the reinforced finger, original sensor housing, both real moving blocks, other installed screws, opposite finger/sensor, plug, moving leads, service loops and tie at 0/50/100 mm commands. The unchanged actuator is loaded from its complete source mesh; separation from its enclosing box proves conservative clearance without approximating its interior. Same-jaw poses are fixed, the approach is outward, opposite-jaw separation increases with opening, and the actuator Z separation is constant. Removal uses the reverse axial path after unscrewing; root screws stay installed. The supplied standalone CAD does not include the robot arm or nearby workcell.

## Engagement and remaining physical checks

The 2.6 mm seat-to-sensor stack gives **1.4 mm nominal penetration** and **0.6 mm nominal margin** to the manual's 2 mm depth. Screw-length tolerance alone gives **1.16…1.64 mm penetration**, leaving at least **0.36 mm**; printed thickness and sensor depth tolerance are not included. The available fully formed thread engagement cannot be inferred from the smooth pilot, tap lead or screw-tip envelope. Thread holding strength and safe tightening torque are therefore UNVERIFIED for every screw. The manufacturer's generic screw torque is not a permissible torque for the sensor or PETG seat.

See [machine measurements](sensor-screw-access.json), [six paths](../drawings/sensor_screw_access.png), [seat section](../drawings/sensor_screw_seating.png), [complete assembly/tool view](../drawings/sensor_screw_access_assembly.png), [interactive complete CAD](../cad/exported/sensor_screw_access.glb), and [local B-rep access study](../cad/exported/sensor_screw_access.step). All measurements are in mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
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
        close[f"S{i}_inserted_pose"] = cad_mesh(Pos(0,0,15)*screw,AMBER)
        close[f"S{i}_axis"] = cad_mesh(cylinder(x,y,P.sensor_screw_seat_z,.25,32),AMBER)
        # Show the engaged shaft locally; full 60 mm shaft/handle in assembly.
        tool = driver_components(x,y)
        local_tool = tool["engaged_hex_tip"]+tool["shaft"]
        local_tool &= box_between(x-2,x+2,y-2,y+2,12,22)
        close[f"S{i}_driver"] = cad_mesh(local_tool,purple)
        for name,shape in ((f"S{i}_screw",screw),(f"S{i}_continuous_insertion",screw_insertion_sweep(x,y)),
                           (f"S{i}_reference_driver",tool["engaged_hex_tip"]+tool["shaft"]+tool["assumed_handle"])):
            shape.label=name;children.append(shape)
    labels = [((x,y,P.sensor_screw_seat_z+16.6),f"S{i}",(-25,-30)) for i,(x,y) in enumerate(P.sensor_axes,1)]
    render(close,V2/"drawings/sensor_screw_access.png",(1.25,-1.4,1.3),
           "Six sensor screws / straight insertion and driver paths",
           "Amber: insertion pose + axis   Steel: seated   Purple: engaged tool segment; one screw at a time",labels,
           up_axis=(0,1,0))
    x,y = P.sensor_axes[2]
    clip = box_between(x-3.3,x+3.3,y,y+3.3,6,24)
    section = {"finger_section":cad_mesh(finger&clip,BLUE),"sensor_section":cad_mesh(sensor&clip,GREEN),
               "screw_section":cad_mesh(sensor_screw(x,y)&clip,STEEL)}
    tool = driver_components(x,y)
    section["driver_section"] = cad_mesh((tool["engaged_hex_tip"]+tool["shaft"])&clip,purple)
    render(section,V2/"drawings/sensor_screw_seating.png",(0,-1,.08),
           "S3 section / same seating stack at all six positions",
           "ISO reference envelope: R0.2 under head / 0.15 x 45 degree seat relief / 0.7 mm hex engagement",
           labels=[((x+1,P.sensor_y_translation-19.00051962584,P.sensor_screw_seat_z),"Local seat relief",(180,-20)),
                   ((x,y,7.8),"1.4 mm nominal penetration",(180,5)),
                   ((x,y,17),"Diameter 3 mm driver / 0.10 radial gap",(180,0))])
    assembly = assembly_meshes(local_meshes(finger,sensor),50)
    location = jaw_location(1,50)
    tool_shape = tool["engaged_hex_tip"]+tool["shaft"]+tool["assumed_handle"]
    assembly["S3_driver_reference_with_assumed_handle"] = cad_mesh(location*tool_shape,purple)
    for i,(x,y) in enumerate(P.sensor_axes,1):
        assembly[f"S{i}_access_axis"] = cad_mesh(location*cylinder(x,y,P.sensor_screw_seat_z,.3,32),AMBER)
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
