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
    # Conservative height of actual surrounding material beside this row.
    region = finger & box_between(-P.width/2,P.width/2,y-2.25,y+2.25,
                                  P.sensor_screw_seat_z(y),P.root_top_z+1)
    return region.bounding_box().max.Z


def verify_sensor_access(finger=None,sensor=None,write=False):
    finger = make_finger() if finger is None else finger
    sensor = placed_sensor() if sensor is None else sensor
    tolerance_p = replace(P,sensor_bore=P.sensor_bore-2*P.sensor_print_radial_error,
                           sensor_access_half_width=P.sensor_access_half_width-P.sensor_print_radial_error,
                           sensor_access_y_min=P.sensor_access_y_min+P.sensor_print_radial_error,
                           sensor_access_y_max=P.sensor_access_y_max-P.sensor_print_radial_error)
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
        assert abs(seat-P.sensor_rear_z-P.sensor_plate_thickness)<1e-8
        assert 2.5 <= seat-P.sensor_rear_z <= 4.0
        # A head-width lateral corridor opens continuously to the central
        # sensor window. No fully enclosed tool tunnel remains above the pad.
        mouth = box_between(min(0,x),max(0,x),y-S.knurled_head_max/2,
                            y+S.knurled_head_max/2,seat+.001,P.root_top_z+1)
        mouth_overlap = volume_common(mouth,finger)
        assert mouth_overlap<1e-7
        # Continuous short flange under the head and access-pocket floor.
        floor_z = P.sensor_rear_z+P.sensor_rear_clearance
        floor = cylinder(x,y,floor_z,2*(P.sensor_access_half_width-abs(x)),seat-floor_z-P.sensor_seat_chamfer)
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
                       "head_seat_type":"continuous planar plate, common rounded rectangular pocket; no counterbore",
                       "common_access_width_mm":2*P.sensor_access_half_width,
                       "lateral_mouth_overlap_mm3":mouth_overlap,
                       "minimum_hole_edge_ligament_mm":min(P.width/2-abs(x),P.tip_y-y,y-P.sensor_frame_proximal_y)-P.sensor_bore/2,
                       "outer_rail_width_mm":P.width/2-P.sensor_access_half_width,
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
                            "knurled_head_radial_sensitivity":(2*(P.sensor_access_half_width-abs(x))-S.knurled_head_max)/2},
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
                                "max_head_radial_clearance_mm":(2*(tolerance_p.sensor_access_half_width-abs(x))-S.knurled_head_max)/2,
                                "shaft_radial_clearance_mm":(tolerance_p.sensor_bore-S.diameter)/2,
                                "path_checks":tolerance_paths},
            "complete_assembly_checks":mechanism_checks,"removal":"PASS for reverse path after unscrewing; finger remains attached"}
        records.append(record)
        print(f"Sensor {name}: reference paths PASS, actual hardware UNVERIFIED; "
              f"min free surface {record['clearance_mm']['minimum_free_surface']:.4f} mm, driver {record['clearance_mm']['driver_shaft']:.3f} mm",flush=True)
    report = {"status":"reference_geometry_passed_actual_hardware_unverified","units":"mm",
        "hardware":asdict(S),"physical_hardware_supplied":False,"full_print_release":False,
        "sensor_source_sha256":sha(SENSOR),"finger_volume_mm3":finger.volume,
        "mounting_geometry":{"plate_thickness_at_screw_mm":P.sensor_plate_thickness,
                             "plate_thickness_over_electronics_mm":P.sensor_plate_thickness-P.sensor_rear_clearance,
                             "common_access_size_xy_mm":[2*P.sensor_access_half_width,P.sensor_access_y_max-P.sensor_access_y_min],
                             "common_access_corner_radius_mm":P.sensor_access_radius,
                             "counterbore_depth_mm":0.0,"outer_rail_width_mm":P.width/2-P.sensor_access_half_width},
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
        export_access(finger,sensor)
    return report


def write_report(report):
    rows = []
    for r in report['screws']:
        c,d = r['clearance_mm'],r['driver']
        rows.append(f"| {r['screw']} | PASS | PASS | PASS | UNVERIFIED | {c['minimum_free_surface']:.4f} | {c['driver_shaft']:.2f} | {d['required_slender_reach_mm']:.2f} |")
    text = f"""# M2324 common screw-access pocket

One **22 × 21.7 mm rounded rectangular pocket, R2 corners**, replaces six individual U pockets and separate pads. A continuous planar seat at Z=12.8 is **3.6 mm** behind the unchanged sensor mounting plane Z=9.2. The six Ø2.1 bores have only a 0.15 × 45° mouth relief; **no head counterbores or screw towers** remain. The plate is 3.0 mm thick over the shallow 0.6 mm electronics clearance and 3.6 mm at the screw-bearing strips. Outer rails are 3.0 mm wide. The R0.4 pocket-floor transition is preserved.

Each head has a fully supported minimum ISO bearing annulus (Ø2.72 outside / Ø2.4 relief). The continuous plate replaces isolated lips and has at least {min(r['seating']['minimum_hole_edge_ligament_mm'] for r in report['screws']):.3f} mm from bore to the external plate edge. Sensor location, 17.5 mm column pitch and 8 mm row pitch are unchanged; each of the six 2 mm blind M1.6 holes is remeasured in the vendor STEP.

S1–S3 are X=−8.75, distal to proximal; S4–S6 are X=+8.75. Six screws per finger, twelve total.

| Screw | Insert / seat | Tighten / remove | Attached-block assembly | Actual hardware | Min free screw clearance (mm) | Driver clearance (mm) | Required blade reach (mm) |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
"""+'\n'.join(rows)+f"""

## Reference fasteners and tool

All six use candidate **M1.6×5**, nominal head **Ø3 × 1.6**, hex **1.5**, pitch **0.35**, per [NBK SNS/SNSS]({S.screw_source}). The [ISO/JIS extract]({S.dimensions_source}) supplies 4.76–5.24 mm length limits, Ø3.14 maximum knurled head, R0.2 under-head blend, Ø2.72 minimum bearing and 0.7 mm minimum socket depth. The CAD includes head, socket and under-head blend; threads use a major-diameter envelope. No physical screw was supplied, so these are parameterized reference dimensions, not a verified BOM.

Reference [Wera 2054 Micro 05118066001]({S.driver_source}): 1.5 mm hex, Ø3 mm shaft, 60 mm blade, modeled 0.7 mm axial engagement. A conservative Ø20 × 97 mm handle is parameterized; its diameter and exact tip transition are unverified. [Product table]({S.driver_product_source}).

Nominal screw penetration is **1.4 mm**, with **0.6 mm** remaining to the manufacturer's 2 mm depth. Screw-length limits plus assumed ±0.15 mm printed-stack error give **1.01–1.79 mm** penetration and **0.21 mm** minimum depth margin. Fully formed thread engagement, tap lead, actual hole depth tolerance and safe torque remain UNVERIFIED. A 6 mm screw would bottom in this stack and is unsuitable.

## Clearance verification

Every seated screw, continuous 30 mm insertion/removal envelope, and driver shaft/handle sweep clears the finger and sensor, both attached moving blocks, the opposite jaw, installed hardware and harness, and the conservative complete-actuator bounding box at 0/50/100 mm. Reverse paths are identical after unscrewing. Same-jaw relative geometry is fixed through travel; separation from the opposing jaw increases with opening. Intended flat-seat and mating-thread contacts are excluded from free-clearance measurements.

Nominal shaft-to-pocket clearance is **0.75 mm radial**. A stated **0.15 mm radial undersize sensitivity** still clears all paths: driver 0.60 mm, screw shank 0.10 mm and under-head blend {min(r['PETG_sensitivity']['minimum_blend_clearance_mm'] for r in report['screws']):.4f} mm. This is not measured PETG printer accuracy. The existing coupon reproduces the 3.6 mm stack and bore-mouth relief. Position error, ovality, support residue and actual hardware fit require physical inspection.

[Mount close-up and section](../drawings/sensor_mount.png) · [Interactive complete assembly/access CAD](../cad/exported/sensor_screw_access.glb) · [Access STEP](../cad/exported/sensor_screw_access.step) · [Machine results](sensor-screw-access.json). PRINT-HOLD remains; no physical assembly or slicing has been validated.
"""
    (V2/'docs/sensor-screw-access.md').write_text(text)


def export_access(finger,sensor):
    from build_v2 import AMBER,assembly_meshes,local_meshes,export_scene
    children = []
    for i,(x,y) in enumerate(P.sensor_axes,1):
        tool = driver_components(x,y)
        for name,shape in ((f'S{i}_screw',sensor_screw(x,y)),
                           (f'S{i}_continuous_insertion',screw_insertion_sweep(x,y)),
                           (f'S{i}_reference_driver',tool['engaged_hex_tip']+tool['shaft']+tool['assumed_handle'])):
            shape.label=name;children.append(shape)
    assembly = assembly_meshes(local_meshes(finger,sensor),50)
    location = jaw_location(1,50)
    tool = driver_components(*P.sensor_axes[2])
    assembly['S3_driver_reference_with_assumed_handle'] = cad_mesh(location*(tool['engaged_hex_tip']+tool['shaft']+tool['assumed_handle']),(155,82,189,255))
    for i,(x,y) in enumerate(P.sensor_axes,1):
        assembly[f'S{i}_access_axis'] = cad_mesh(location*cylinder(x,y,P.sensor_screw_seat_z(y),.3,32),AMBER)
    export_scene(assembly,V2/'cad/exported/sensor_screw_access.glb')
    for name,shape in (('reinforced_finger',finger),('M2324',sensor),
                       ('retained_moving_block',faceted_solid(carrier_and_finger(1)[0]))):
        shape = Pos(0,0,0)*shape;shape.label=name;children.append(shape)
    export_step(Compound(children=children,label='Local access alternatives; complete actuator in GLB'),
                V2/'cad/exported/sensor_screw_access.step')


if __name__=='__main__':
    verify_sensor_access(write=True)
