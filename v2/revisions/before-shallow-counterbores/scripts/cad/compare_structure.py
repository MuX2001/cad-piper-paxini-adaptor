"""Actual-section beam comparison, not FEA or a printed-part strength rating.

Units: mm, N, MPa. Beam axis is native jaw Y. Loads act at the unchanged
distal contact datum Y=0; the root Y=-70 is ideally clamped. All holes count.
"""

import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(V2 / "cad/source"))

import numpy as np
from build123d import Box, Plane, import_step
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from PIL import Image, ImageDraw

from references import cad_mesh
from replacement_finger import P, make_finger
from render import font, render

MATERIAL_URL = "https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf"
BEAM_URL = "https://ocw.mit.edu/courses/16-01-unified-engineering-i-ii-iii-iv-fall-2005-spring-2006/f66f80cd5fbd5cf8295d7b1e1e28a368_gm5_8_notes.pdf"
E_REFERENCE = 1810.0  # PETG HF TDS v1.0 Young's modulus XY; NOT actual filament measurement.
DENSITY = 1.28  # g/cm^3, same reference, fully dense material-equivalent estimate.
NORMAL_LOAD = 25.0  # Representative only; supplied sensor measurement range, not allowable load.
LATERAL_LOAD = 10.0


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(shape,y):
    return shape & Plane(origin=(0,y,0),x_dir=(1,0,0),z_dir=(0,1,0))


def area_properties(shape):
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape.wrapped,props)
    inertia = props.MatrixOfInertia()
    # Covariance integral of (x,z); GProp's off-diagonal inertia is minus x*z.
    covariance = np.array([[inertia.Value(3,3),-inertia.Value(1,3)],
                           [-inertia.Value(3,1),inertia.Value(1,1)]])
    return props.Mass(),np.array(props.CentreOfMass().Coord())[[0,2]],covariance


def section_properties(shape,y):
    cut = section(shape,y)
    area,center,cov = area_properties(cut)
    assert area > 0 and np.linalg.eigvalsh(cov).min() > 0
    independent = sum((area_properties(f)[2] for f in cut.faces()),np.zeros((2,2)))
    bb = cut.bounding_box()
    corners = np.array([(x,z) for x in (bb.min.X,bb.max.X) for z in (bb.min.Z,bb.max.Z)])-center
    inv = np.linalg.inv(cov)
    lever = max(0,-y)
    return {"y_mm":float(y),"area_mm2":float(area),"centroid_x_mm":float(center[0]),
            "centroid_z_mm":float(center[1]),"Ixx_mm4":float(cov[1,1]),"Izz_mm4":float(cov[0,0]),
            "product_xz_mm4":float(cov[0,1]),"polar_area_moment_mm4":float(np.trace(cov)),
            "effective_I_grip_mm4":float(1/inv[1,1]),"effective_I_lateral_mm4":float(1/inv[0,0]),
            "independent_faces_I_grip_mm4":float(1/np.linalg.inv(independent)[1,1]),
            "independent_faces_I_lateral_mm4":float(1/np.linalg.inv(independent)[0,0]),
            "nominal_normal_stress_mpa":float(np.abs(corners @ (inv @ [0,NORMAL_LOAD*lever])).max()),
            "nominal_lateral_stress_mpa":float(np.abs(corners @ (inv @ [LATERAL_LOAD*lever,0])).max()),
            "connected_faces":len(cut.faces()),"inner_loops":sum(len(f.inner_wires()) for f in cut.faces())}


def beam_integral(shape,spacing,cache):
    count = round(-P.mount_y/spacing)
    dy = -P.mount_y/count
    stations = P.mount_y+(np.arange(count)+.5)*dy
    rows = []
    for y in stations:
        key = round(float(y),8)
        if key not in cache:
            cache[key] = section_properties(shape,float(y))
        rows.append(cache[key])
    def compliance(field):
        return sum(r["y_mm"]**2/r[field]*dy for r in rows)
    values = {"grip":compliance("effective_I_grip_mm4"),
              "lateral":compliance("effective_I_lateral_mm4"),
              "grip_independent_faces":compliance("independent_faces_I_grip_mm4"),
              "lateral_independent_faces":compliance("independent_faces_I_lateral_mm4")}
    volume = sum(r["area_mm2"]*dy for r in rows)
    # Include the distal holder overhang for the independent area/volume check.
    n = int(np.ceil(P.tip_y/spacing))
    for y in (np.arange(n)+.5)*P.tip_y/n:
        key = round(float(y),8)
        if key not in cache:
            cache[key] = section_properties(shape,float(y))
        volume += cache[key]["area_mm2"]*P.tip_y/n
    return values,volume,rows


def analyze(shape):
    cache = {}
    coarse,_,_ = beam_integral(shape,1.0,cache)
    fine,section_volume,rows = beam_integral(shape,.5,cache)
    convergence = {k:abs(coarse[k]/fine[k]-1) for k in fine}
    assert max(convergence.values()) < .03, convergence
    assert abs(section_volume/shape.volume-1) < .01
    samples = [section_properties(shape,y) for y in (-69,-60,-50,-35,-15)]
    result = {"volume_mm3":shape.volume,"solid_material_mass_g":shape.volume*DENSITY/1000,
              "bounds_mm":[tuple(shape.bounding_box().min),tuple(shape.bounding_box().max)],
              "section_samples":samples,"integration_step_mm":.5,
              "coarse_fine_relative_change":convergence,"section_integral_volume_mm3":section_volume,
              "section_volume_relative_error":abs(section_volume/shape.volume-1),
              "nominal_root_normal_stress_mpa":max(r["nominal_normal_stress_mpa"] for r in rows if r["y_mm"] <= -55),
              "nominal_max_normal_stress_mpa":max(r["nominal_normal_stress_mpa"] for r in rows),
              "nominal_max_lateral_stress_mpa":max(r["nominal_lateral_stress_mpa"] for r in rows),
              "nominal_peak_normal_y_mm":max(rows,key=lambda r:r["nominal_normal_stress_mpa"])["y_mm"]}
    for direction,load in (("grip",NORMAL_LOAD),("lateral",LATERAL_LOAD)):
        result[direction] = {"load_n":load,"tip_deflection_mm":load*fine[direction]/E_REFERENCE,
            "tip_stiffness_n_per_mm":E_REFERENCE/fine[direction],
            "equivalent_I_mm4":(-P.mount_y)**3/(3*fine[direction]),
            "half_modulus_tip_deflection_mm":2*load*fine[direction]/E_REFERENCE,
            "independent_faces_tip_deflection_mm":load*fine[direction+"_independent_faces"]/E_REFERENCE}
    return result,rows


def draw_sections(previous,current):
    im = Image.new("RGB",(1440,1080),(245,247,250))
    draw = ImageDraw.Draw(im)
    draw.text((30,20),"Actual CAD sections / identical scale / native jaw X-Z planes",font=font(27),fill="#142c45")
    draw.text((30,65),"Top: previous V2     Bottom: reinforced V2     Holes and rounded cores included",font=font(19),fill="#46576b")
    for row,(name,part,color) in enumerate((("Previous",previous,"#8d99a8"),("Reinforced",current,"#277bc4"))):
        for col,y in enumerate((-60,-35,-15)):
            cut = section(part,y)
            props = section_properties(part,y)
            x0,y0 = col*480,row*445+120
            draw.text((x0+28,y0),f"{name} / Y = {y:g} mm",font=font(22),fill="#142c45")
            def polygon(wire):
                return [(x0+240+v.X*10,y0+350-v.Z*10)
                        for v in (wire.position_at(t) for t in np.linspace(0,1,400,endpoint=False))]
            for face in cut.faces():
                draw.polygon(polygon(face.outer_wire()),fill=color)
                for wire in face.inner_wires():
                    draw.polygon(polygon(wire),fill="#f5f7fa")
            draw.text((x0+28,y0+365),f"A {props['area_mm2']:.1f} mm²   Ixx {props['Ixx_mm4']:.0f} mm⁴",font=font(18),fill="#46576b")
            draw.text((x0+28,y0+394),f"Izz {props['Izz_mm4']:.0f} mm⁴   {props['connected_faces']} connected section(s)",font=font(17),fill="#46576b")
    draw.text((30,1040),"Geometric properties only. Ixx: gripping-plane bending; Izz: lateral bending. Neither is torsional J.",font=font(18),fill="#46576b")
    im.save(V2 / "drawings/structural_sections.png")


def comparison_preview(previous,current):
    direction = np.array((1.3,1.8,1.4));direction /= np.linalg.norm(direction)
    right = np.cross((0,-1,0),direction);right /= np.linalg.norm(right)
    meshes = [cad_mesh(previous,(141,153,168,255)),cad_mesh(current)]
    distance = max(np.ptp(m.vertices @ right) for m in meshes)+18
    for sign,mesh in zip((-1,1),meshes):
        mesh.apply_translation(sign*distance/2*right)
    render(dict(zip(("previous","reinforced"),meshes)),V2/"drawings/v2_structural_comparison.png",direction,
           "Previous V2 / reinforced V2 — same scale, same 70 mm tactile reach",
           "Grey: 3 mm open ribs / 4 mm root seat     Blue: 5 mm webs, partial box, radiused root / 6 mm seat",
           up_axis=(0,-1,0))


def compare_structure(current=None):
    current = make_finger() if current is None else current
    archive = json.loads((V2/"docs/previous-revision.json").read_text())
    old_path = V2/archive["snapshot"]/"cad/exported/replacement_finger.step"
    assert digest(old_path) == archive["files"]["cad/exported/replacement_finger.step"]
    previous = import_step(old_path)
    old_params = json.loads((V2/archive["snapshot"]/"docs/build-manifest.json").read_text())["parameters"]
    for key in ("mount_y","width","tip_y","sensor_y_translation","sensor_rear_z","sensor_screw_length",
                "plug_center_x","socket_mouth_native_y","straight_exit","cable_bend_radius","fixed_loom_x"):
        assert old_params[key] == asdict(P)[key], f"Functional datum changed: {key}"
    # Independent analytical sanity check for the area-property extraction.
    rectangle = section_properties(Box(10,20,30),0)
    assert abs(rectangle["area_mm2"]-300) < 1e-7
    assert abs(rectangle["Ixx_mm4"]-22500) < 1e-6
    assert abs(rectangle["Izz_mm4"]-2500) < 1e-6
    records,rows = {},[]
    for name,shape in (("previous",previous),("reinforced",current)):
        records[name],data = analyze(shape)
        rows.extend({"revision":name,**r} for r in data)
        print(f"Structure: {name}, {records[name]['solid_material_mass_g']:.2f} g solid-equivalent, "
              f"25 N beam deflection {records[name]['grip']['tip_deflection_mm']:.4f} mm",flush=True)
    old,new = records["previous"],records["reinforced"]
    ratios = {"mass":new["solid_material_mass_g"]/old["solid_material_mass_g"],
              "grip_stiffness":new["grip"]["tip_stiffness_n_per_mm"]/old["grip"]["tip_stiffness_n_per_mm"],
              "lateral_stiffness":new["lateral"]["tip_stiffness_n_per_mm"]/old["lateral"]["tip_stiffness_n_per_mm"],
              "root_nominal_stress":new["nominal_root_normal_stress_mpa"]/old["nominal_root_normal_stress_mpa"]}
    assert ratios["grip_stiffness"] > 1 and ratios["lateral_stiffness"] > 1 and ratios["root_nominal_stress"] < 1
    closed = next(r for r in new["section_samples"] if r["y_mm"] == -35)
    assert closed["connected_faces"] == 1 and closed["inner_loops"] == 1
    report = {"status":"comparative_calculation_passed","physical_strength_verified":False,
        "baseline_commit":archive["git_commit"],"baseline_step_sha256":digest(old_path),
        "material":{"reference":"Bambu PETG HF TDS V1.0; actual filament grade/process unverified",
                    "source":MATERIAL_URL,"youngs_xy_mpa":E_REFERENCE,"youngs_z_mpa":1540,
                    "density_g_per_cm3":DENSITY,"reference_test_infill_percent":100,
                    "reference_samples_annealed":True,"actual_effective_modulus_mpa":None},
        "method":{"source":BEAM_URL,"description":"Euler-Bernoulli variable-section beam; exact planar B-rep area properties, including holes; covariance inversion includes unsymmetrical sections; midpoint integration",
                  "root_y_mm":P.mount_y,"point_load_y_mm":0,"loads_n":{"grip":NORMAL_LOAD,"lateral":LATERAL_LOAD},
                  "load_basis":"Representative values from supplied M2324 measurement ranges (25 N normal / 10 N tangential), NOT an allowable force or actual robot operating force",
                  "tip_deflection_formula":"delta = F/E * integral((0-y)^2 / I_effective(y) dy)",
                  "stress_formula":"sigma_y = [x-cx,z-cz] @ inverse(area covariance) @ [Mz,Mx]; bounding-corner envelope",
                  "coupling_sensitivity":"Independent-face alternative omits parallel-axis coupling between disconnected section faces; a frame-model sensitivity, not a rigorous bound",
                  "limits":["Ideal root clamp; excludes screw/contact compliance and sensor housing flexibility",
                            "Homogeneous solid-equivalent modulus; excludes shear deformation, FDM defects, creep and delamination",
                            "Beam nominal stress only; no local notch stress, fatigue life, safety factor or strength rating",
                            "Polar area moment is NOT Saint-Venant torsional rigidity; full torsional deflection unverified"]},
        "torsion":{"section_y_mm":-35,"previous_connected_faces":2,"reinforced_connected_faces":1,
                   "reinforced_closed_cell_count":1,"twist_degrees":None,
                   "assessment":"Closed mid-span cell couples the webs and provides a shear-flow path; the necessary root service opening and sensor window remain locally open and can govern twist/warping."},
        "root_bolt_group":{"normal_load_moment_nmm":NORMAL_LOAD*(-P.mount_y),
                           "elastic_bolt_only_peak_axial_n":NORMAL_LOAD*(-P.mount_y)*4/(4*4**2),
                           "equal_transverse_shear_per_screw_n":NORMAL_LOAD/4,
                           "interpretation":"Unchanged four-bolt 12 x 8 pattern; illustrative elastic bolt-only moment sharing, no preload/friction/contact model. Real engagement, preload, plastic bearing and cyclic loads require verification."},
        "previous":old,"reinforced":new,"ratios":ratios}
    (V2/"docs/mechanical-comparison.json").write_text(json.dumps(report,indent=2)+"\n")
    with (V2/"docs/section-properties.csv").open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write_summary(report)
    draw_sections(previous,current)
    comparison_preview(previous,current)
    return report


def write_summary(report):
    a,b = report["previous"],report["reinforced"]
    text = f"""# Previous versus reinforced V2

Baseline: `{report['baseline_commit']}`; all 47 previous V2 files retained in `../revisions/goal-02/` and checked against `previous-revision.json`.

| Metric | Previous V2 | Reinforced V2 |
| --- | ---: | ---: |
| Width × length × depth | 28 × 73.2 × 22.5 mm | 28 × 73.2 × 27 mm |
| Tactile reach from original mount | 70.000 mm | 70.000 mm |
| Solid-material mass estimate, same density | {a['solid_material_mass_g']:.2f} g | {b['solid_material_mass_g']:.2f} g |
| Root bearing thickness / nominal engagement | 4 / 2 mm, M2×6 | 6 / 2 mm, M2×8 |
| Web / skin / sensor rail thickness | 3 / open / 4 mm | 5 / 3.5 / 5.5 mm; Ø6 sensor bosses |
| Mid-span Y=−35 area | {a['section_samples'][3]['area_mm2']:.1f} mm² | {b['section_samples'][3]['area_mm2']:.1f} mm² |
| Mid-span Ixx / Izz | {a['section_samples'][3]['Ixx_mm4']:.0f} / {a['section_samples'][3]['Izz_mm4']:.0f} mm⁴ | {b['section_samples'][3]['Ixx_mm4']:.0f} / {b['section_samples'][3]['Izz_mm4']:.0f} mm⁴ |
| Matched gripping tip stiffness, ideal beam | {a['grip']['tip_stiffness_n_per_mm']:.1f} N/mm | {b['grip']['tip_stiffness_n_per_mm']:.1f} N/mm |
| Estimated gripping deflection at 25 N | {a['grip']['tip_deflection_mm']:.4f} mm | {b['grip']['tip_deflection_mm']:.4f} mm |
| Estimated lateral deflection at 10 N, coupled sections | {a['lateral']['tip_deflection_mm']:.4f} mm | {b['lateral']['tip_deflection_mm']:.4f} mm |
| Lateral deflection with independent-face assumption | {a['lateral']['independent_faces_tip_deflection_mm']:.4f} mm | {b['lateral']['independent_faces_tip_deflection_mm']:.4f} mm |
| Root-region maximum nominal bending stress at 25 N | {a['nominal_root_normal_stress_mpa']:.2f} MPa | {b['nominal_root_normal_stress_mpa']:.2f} MPa |
| Transition / opening corner radii | Sharp large windows | R2.5 outer transitions, R2 core, R3 service window |
| Torsion / warping | Separate open rails | Closed mid-span cell; root service and sensor windows remain open |
| Print orientation and supports | X=−14 side down; exposed large spans | Same orientation; short core roof bridges; external accessible supports |

Geometry-only beam comparison: **{report['ratios']['grip_stiffness']:.2f}× gripping stiffness**, **{report['ratios']['lateral_stiffness']:.2f}× coupled-section lateral stiffness**, with **{(report['ratios']['mass']-1)*100:.1f}%** more solid-material mass. These are estimates under matched assumptions, not measured performance. The lateral independent-face result shows sensitivity to cross-section coupling; the open baseline is particularly sensitive. No whole-finger torsional stiffness multiplier is claimed.

Calculations use actual CAD slices every 0.5 mm, including bores/windows, with 1 mm convergence and section-area/solid-volume checks. The [JSON](mechanical-comparison.json) records all assumptions and checks; [CSV](section-properties.csv) contains the section properties. Loads act at distal Y=0, with an ideal clamp at Y=−70. The 25 N normal and 10 N lateral loads are representative sensor measurement-range values from the supplied manual, not allowable grip forces. Shear deformation, bolted-joint motion and sensor-housing flexibility are excluded. [Beam method]({BEAM_URL}).

Material reference: **E=1810 MPa** along printed XY and **density 1.28 g/cm³**, from [Bambu PETG HF TDS V1.0]({MATERIAL_URL}). The user's actual PETG grade and printed properties are unknown. The reference used 100% infill and annealed test specimens; do not assume this part reproduces them. At an assumed half modulus (905 MPa), gripping deflections double to **{a['grip']['half_modulus_tip_deflection_mm']:.4f} / {b['grip']['half_modulus_tip_deflection_mm']:.4f} mm**. This is a sensitivity case, not a validated lower stiffness limit. Mass excludes supports, hardware and real print voids; no slicer or weighing result is implied.

Side printing keeps longitudinal Y fibres and gripping-plane Y–Z load paths within layers. Lateral and torsional loading still impose interlayer shear and splitting risks. Rounded transitions remove sharp geometric notches, but local stress concentration, creep and fatigue life remain unverified. The unchanged root bolt pattern still carries the 1750 N·mm representative root moment; a simplistic bolt-only elastic split gives about 109 N axial load per tension-row screw. Real preload, contact load sharing, thread engagement and polymer bearing must be checked; no torque or safety factor is assigned.

See [manufacturing and assembly notes](manufacturing.md), [actual CAD sections](../drawings/structural_sections.png) and [same-scale CAD comparison](../drawings/v2_structural_comparison.png). Existing PRINT-HOLD remains in force.
"""
    (V2/"docs/mechanical-comparison.md").write_text(text)


if __name__ == "__main__":
    compare_structure()
