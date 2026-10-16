"""Measure actual CAD sections before/after simplification; no strength rating."""
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / 'cad/source'))
import numpy as np
from build123d import Box, Compound, Plane, import_step
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from replacement_finger import P, make_finger, box_between


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(shape, y):
    return shape & Plane(origin=(0,y,0), x_dir=(1,0,0), z_dir=(0,1,0))


def section_properties(shape, y):
    cut = section(shape,y)
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(cut.wrapped, props)
    inertia = props.MatrixOfInertia()
    assert props.Mass() > 0
    return {'y_mm':float(y), 'area_mm2':props.Mass(),
            'Ixx_mm4':inertia.Value(1,1), 'Izz_mm4':inertia.Value(3,3),
            'connected_faces':len(cut.faces()),
            'inner_loops':sum(len(f.inner_wires()) for f in cut.faces())}


def compare_structure(current=None):
    current = make_finger() if current is None else current
    archive = json.loads((V2/'docs/pre-simplification-revision.json').read_text())
    path = V2/archive['snapshot']/'cad/exported/replacement_finger.step'
    assert digest(path) == archive['files']['cad/exported/replacement_finger.step']
    previous = import_step(path)
    old_params = json.loads((V2/archive['snapshot']/'docs/build-manifest.json').read_text())['parameters']
    unchanged = ('mount_y','width','tip_y','flange_thickness','root_top_z','sensor_y_translation',
                 'sensor_rear_z','sensor_hole_x','sensor_hole_y','sensor_bore','plug_center_x',
                 'socket_mouth_native_y','straight_exit','cable_bend_radius','fixed_loom_x',
                 'rib_thickness','arm_flange_thickness')
    for key in unchanged:
        assert json.loads(json.dumps(asdict(P)[key])) == old_params[key], key
    # Imported STEP is compared with current parametric B-rep. Reject bad booleans.
    root = box_between(-15,15,-71,-56,0,40)
    root_old, root_new = previous & root, current & root
    differences = (root_old-root_new,root_new-root_old)
    assert all(d.is_valid for d in differences)
    root_change = sum(d.volume for d in differences)
    assert root_change < 1e-6
    rails = Compound(children=[box_between(a,b,P.sensor_frame_proximal_y,P.tip_y,0,40)
                               for a,b in ((-14,-11.001),(11.001,14))])
    rails_old, rails_new = previous & rails, current & rails
    rail_cuts = (rails_old-rails_new,rails_new-rails_old)
    assert all(d.is_valid for d in rail_cuts)
    rail_change = sum(d.volume for d in rail_cuts)
    assert rail_change<1e-6
    assert np.allclose(tuple(current.bounding_box().min),tuple(previous.bounding_box().min),atol=1e-6)
    assert np.allclose(tuple(current.bounding_box().max),tuple(previous.bounding_box().max),atol=1e-6)
    rectangle = section_properties(Box(10,20,30),0)
    assert abs(rectangle['area_mm2']-300)<1e-7 and abs(rectangle['Ixx_mm4']-22500)<1e-6
    records, rows = {}, []
    for name, shape in (('previous',previous),('simplified',current)):
        samples = [section_properties(shape,y) for y in (-69,-60,-50,-35,-15)]
        records[name] = {'volume_mm3':shape.volume, 'face_count':len(shape.faces()),
                         'section_samples':samples,
                         'bounds_mm':[tuple(shape.bounding_box().min),tuple(shape.bounding_box().max)]}
        rows.extend({'revision':name, **r} for r in samples)
    ratios = []
    for old,new in zip(records['previous']['section_samples'],records['simplified']['section_samples']):
        row = {'y_mm':new['y_mm'], **{k:new[k]/old[k] for k in ('area_mm2','Ixx_mm4','Izz_mm4')}}
        if new['y_mm'] <= -35:
            assert min(row[k] for k in ('area_mm2','Ixx_mm4','Izz_mm4')) >= 1-1e-6
        ratios.append(row)
    middle = records['simplified']['section_samples'][3]
    assert middle['connected_faces']==1 and middle['inner_loops']==0
    report = {'status':'section_preservation_passed','units':'mm',**records,
              'root_boolean_difference_mm3':root_change, 'outer_rail_difference_mm3':rail_change, 'unchanged_parameters':unchanged,
              'section_ratios':ratios, 'enclosed_arm_core_removed':True,
              'limits':'Geometric section checks only. No quantified PETG strength, stiffness, creep or fatigue claim.'}
    (V2/'docs/mechanical-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    with (V2/'docs/section-properties.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    table = '\n'.join(f"| {r['y_mm']:g} | {r['area_mm2']:.3f} | {r['Ixx_mm4']:.3f} | {r['Izz_mm4']:.3f} |" for r in ratios)
    (V2/'docs/mechanical-comparison.md').write_text(f'''# V2 simplification: measured CAD sections

The root region Y ≤ −56 is unchanged by exact solid comparison (difference {root_change:.6f} mm³). The outside bounds, functional datums and continuous sensor outer rails are unchanged (rail difference {rail_change:.6f} mm³). Filling the enclosed arm core leaves a continuous solid middle section; no new ribs or external reinforcement were added.

CAD faces: **{len(previous.faces())} → {len(current.faces())}**. Volume: **{previous.volume:.1f} → {current.volume:.1f} mm³**. The existing cable saddle is one concentric circular section instead of a nine-section loft.

| Native Y (mm) | Area ratio | Ixx ratio | Izz ratio |
| ---: | ---: | ---: | ---: |
{table}

Ratios are simplified / previous reinforced V2. Root and arm sections preserve or increase these geometric properties. The sensor section deliberately replaces tall pocket-dividing walls with a continuous short seating plate, while retaining the outer rails. These area moments are not printed-part strength predictions. Local clamping, creep and fatigue remain physically unverified.

[Full measurements](mechanical-comparison.json) · [Section CSV](section-properties.csv) · [Preserved previous revision](../revisions/before-geometry-simplification/README.md)
''')
    print(f"Simplification: {len(previous.faces())} -> {len(current.faces())} faces; root unchanged; arm core filled",flush=True)
    return report


if __name__ == '__main__':
    compare_structure()
