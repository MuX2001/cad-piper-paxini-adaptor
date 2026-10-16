"""Bounded PETG acceptance audit of the six active V2 printable STL exports.

Mesh intersection checks use an exhaustive AABB sweep, triangle plane clipping
and coplanar edge/containment tests. Only contact on the indexed common vertex
or edge is permitted. No mesh repair, slicer emulation or strength claim.
"""

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / "cad/source"))

import numpy as np
import trimesh

EPS = 1e-6  # mm: numerical intersection tolerance, not a printing allowance.
PLANE_EPS = 1e-10  # Never snap nearby vertices onto nearly parallel planes.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross2(a, b):
    return a[0]*b[1]-a[1]*b[0]


def inside2(point, triangle):
    edges = np.roll(triangle, -1, axis=0)-triangle
    signs = np.array([cross2(edge, point-base)/np.linalg.norm(edge)
                      for base, edge in zip(triangle, edges)])
    return bool(np.all(signs >= -EPS) or np.all(signs <= EPS))


def segment_contacts2(a, b, c, d):
    r, s, q = b-a, d-c, c-a
    lr, ls = np.linalg.norm(r), np.linalg.norm(s)
    den = cross2(r, s)
    if abs(den) > 1e-12*lr*ls:
        t, u = cross2(q, s)/den, cross2(q, r)/den
        if -EPS/lr <= t <= 1+EPS/lr and -EPS/ls <= u <= 1+EPS/ls:
            return [a+np.clip(t, 0, 1)*r]
    elif abs(cross2(q, r))/lr <= EPS:
        t0, t1 = sorted((np.dot(c-a, r)/(lr*lr), np.dot(d-a, r)/(lr*lr)))
        lo, hi = max(0, t0), min(1, t1)
        if lo <= hi+EPS/lr:
            return [a+np.clip(lo, 0, 1)*r, a+np.clip(hi, 0, 1)*r]
    return []


def allowed_contacts(points, shared):
    if not len(points):
        return True
    if not len(shared):
        return False
    points, shared = np.asarray(points), np.asarray(shared)
    if len(shared) == 1:
        return bool(np.max(np.linalg.norm(points-shared[0], axis=1)) <= 2*EPS)
    edge = shared[1]-shared[0]
    t = np.clip((points-shared[0]) @ edge/(edge @ edge), 0, 1)
    return bool(np.max(np.linalg.norm(points-shared[0]-t[:, None]*edge, axis=1)) <= 2*EPS)


def plane_segment(triangle, distances):
    points = [p for p, d in zip(triangle, distances) if abs(d) <= PLANE_EPS]
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = distances[i], distances[j]
        if (a < -PLANE_EPS and b > PLANE_EPS) or (a > PLANE_EPS and b < -PLANE_EPS):
            points.append(triangle[i]+a/(a-b)*(triangle[j]-triangle[i]))
    return np.asarray(points)


def improper_intersection(a, b, na, nb, da, db, shared):
    """Distances da are A to B's plane; db are B to A's plane."""
    coplanar = np.max(np.abs(da)) <= PLANE_EPS and np.max(np.abs(db)) <= PLANE_EPS
    if coplanar:
        keep = [i for i in range(3) if i != np.argmax(np.abs(na))]
        aa, bb = a[:, keep], b[:, keep]
        contacts = [p for p in aa if inside2(p, bb)] + [p for p in bb if inside2(p, aa)]
        for i in range(3):
            for j in range(3):
                contacts.extend(segment_contacts2(aa[i], aa[(i+1)%3], bb[j], bb[(j+1)%3]))
        return not allowed_contacts(contacts, shared[:, keep])
    # Noncoplanar triangles with a common edge can only meet on that edge.
    if len(shared) == 2:
        return False
    direction = np.cross(na, nb)
    length = np.linalg.norm(direction)
    if length < 1e-12:
        return False  # Parallel distinct planes; coplanarity handled above.
    direction /= length
    pa, pb = plane_segment(a, da), plane_segment(b, db)
    if not len(pa) or not len(pb):
        return False
    ta, tb = pa @ direction, pb @ direction
    lo, hi = max(ta.min(), tb.min()), min(ta.max(), tb.max())
    if hi < lo-EPS:
        return False
    if not len(shared):
        return True
    common = float(shared[0] @ direction)
    return lo < common-2*EPS or hi > common+2*EPS


def self_intersections(mesh):
    triangles = mesh.triangles
    lo, hi = triangles.min(axis=1), triangles.max(axis=1)
    # Longest global axis reduces the candidate set; other axes are also tested.
    axis = int(np.argmax(mesh.extents))
    order = np.argsort(lo[:, axis], kind="stable")
    starts = lo[order, axis]
    broad, narrow, count, examples = 0, 0, 0, []
    normals = mesh.face_normals
    for rank, i in enumerate(order):
        end = np.searchsorted(starts, hi[i, axis]+EPS, side="right")
        candidates = order[rank+1:end]
        candidates = candidates[np.all(lo[candidates] <= hi[i]+EPS, axis=1) &
                                np.all(hi[candidates] >= lo[i]-EPS, axis=1)]
        broad += len(candidates)
        if not len(candidates):
            continue
        db = (triangles[candidates]-triangles[i, 0]) @ normals[i]
        da = np.einsum("ijk,ik->ij", triangles[i]-triangles[candidates, 0, None], normals[candidates])
        eligible = ~((db.min(axis=1) > EPS) | (db.max(axis=1) < -EPS) |
                     (da.min(axis=1) > EPS) | (da.max(axis=1) < -EPS))
        for j, d1, d2 in zip(candidates[eligible], da[eligible], db[eligible]):
            narrow += 1
            common = np.intersect1d(mesh.faces[i], mesh.faces[j], assume_unique=True)
            if improper_intersection(triangles[i], triangles[j], normals[i], normals[j],
                                     d1, d2, mesh.vertices[common]):
                count += 1
                if len(examples) < 20:
                    examples.append([int(i), int(j)])
    return {"aabb_pairs": broad, "plane_clip_pairs": narrow,
            "improper_triangle_intersections": count, "example_face_pairs": examples,
            "numerical_tolerance_mm": EPS}


def nonmanifold_vertices(mesh):
    # Each vertex link of a closed 2-manifold must be one cycle, not two fans.
    links = defaultdict(list)
    for a, b, c in mesh.faces:
        links[a].append((b, c)); links[b].append((c, a)); links[c].append((a, b))
    invalid = []
    for vertex, pairs in links.items():
        graph = defaultdict(list)
        for a, b in pairs:
            graph[a].append(b); graph[b].append(a)
        pending, visited = [next(iter(graph))], set()
        while pending:
            v = pending.pop()
            if v not in visited:
                visited.add(v)
                pending.extend(graph[v])
        if len(visited) != len(graph) or any(len(v) != 2 for v in graph.values()):
            invalid.append(int(vertex))
    return invalid


def check_intersection_kernel():
    """Small analytic cases guard against accepting every closed mesh by default."""
    a = np.array([[0., 0, 0], [2, 0, 0], [0, 2, 0]])
    fixtures = [
        ("crossing", [[.5, .5, -1], [.5, .5, 1], [1, .5, 0]], [], True),
        ("coplanar_overlap", [[.5, .5, 0], [2, .5, 0], [.5, 2, 0]], [], True),
        ("parallel_separated", [[0, 0, 1], [2, 0, 1], [0, 2, 1]], [], False),
        ("coplanar_disjoint", [[1.5, 1.5, 0], [3, 1.5, 0], [1.5, 3, 0]], [], False),
        ("shared_edge", [[0, 0, 0], [2, 0, 0], [0, -2, 0]], [a[0], a[1]], False),
        ("folded_overlap", [[0, 0, 0], [2, 0, 0], [1, 1, 0]], [a[0], a[1]], True),
        ("shared_vertex", [[0, 0, 0], [-1, -1, -1], [-1, -1, 1]], [a[0]], False),
        ("crossing_beyond_vertex", [[0, 0, 0], [1, 1, -1], [1, 1, 1]], [a[0]], True),
        ("unindexed_touch", [[0, 0, 0], [-1, 0, 0], [0, -1, 0]], [], True),
    ]
    for name, b, shared, expected in fixtures:
        b = np.array(b, dtype=float)
        na, nb = np.cross(a[1]-a[0], a[2]-a[0]), np.cross(b[1]-b[0], b[2]-b[0])
        na /= np.linalg.norm(na); nb /= np.linalg.norm(nb)
        da, db = (a-b[0]) @ nb, (b-a[0]) @ na
        result = improper_intersection(a, b, na, nb, da, db, np.asarray(shared).reshape(-1, 3))
        assert result == expected, (name, result, expected)
    return [f[0] for f in fixtures]


def audit_mesh(path):
    # process=False preserves exported facets; only exact/repeated vertices merge.
    mesh = trimesh.load_mesh(path, process=False)
    assert np.isfinite(mesh.vertices).all(), path
    mesh.merge_vertices(digits_vertex=8)
    edge_counts = np.bincount(mesh.edges_unique_inverse)
    vertex_errors = nonmanifold_vertices(mesh)
    intersections = self_intersections(mesh)
    result = {"sha256": sha(path), "vertices": len(mesh.vertices), "facets": len(mesh.faces),
              "watertight": bool(mesh.is_watertight), "consistent_winding": bool(mesh.is_winding_consistent),
              "surface_components": int(mesh.body_count), "positive_volume": bool(mesh.volume > 0),
              "edges_without_two_faces": int(np.count_nonzero(edge_counts != 2)),
              "nonmanifold_vertices": len(vertex_errors), "degenerate_faces": int((mesh.area_faces <= 1e-12).sum()),
              "duplicate_faces": int((~mesh.unique_faces()).sum()), "minimum_facet_area_mm2": float(mesh.area_faces.min()),
              "bounds_mm": mesh.bounds.tolist(), **intersections}
    result["result"] = "PASS" if (result["watertight"] and result["consistent_winding"] and
        result["positive_volume"] and result["surface_components"] == 1 and all(result[k] == 0 for k in
        ("edges_without_two_faces", "nonmanifold_vertices", "degenerate_faces", "duplicate_faces", "improper_triangle_intersections"))) else "FAIL"
    print(f"Mesh {path.name}: {result['result']}, {len(mesh.faces)} facets, "
          f"{intersections['improper_triangle_intersections']} improper intersections", flush=True)
    return result


def check_skin_correction(finger):
    """Compare the authoritative source solid to the archived STEP geometry."""
    from build123d import Face, Solid, Wire, import_step
    from replacement_finger import P
    archive = json.loads((V2/"docs/pre-printability-revision.json").read_text())
    old = import_step(V2/archive["snapshot"]/"cad/exported/replacement_finger.step")
    removed, added = old-finger, finger-old
    half = P.width/2-P.rib_thickness
    y0, y1 = P.root_block_end_y, P.sensor_frame_proximal_y
    z0, z1 = P.root_top_z-P.arm_flange_thickness, P.arm_distal_top_z-P.arm_flange_thickness
    # Includes the existing R2 top-edge fillets, whose centres move with the roof.
    # The sloped-roof/end-wall fillet tangent extends R*(sec(angle)+tan(angle))
    # vertically; a plain R-deep band would incorrectly exclude its end arc.
    band_depth = P.core_fillet*((1+P.arm_rear_slope**2)**.5+abs(P.arm_rear_slope)) + P.rear_skin_vertical_offset-P.arm_flange_thickness+.01
    zone = Solid.extrude(Face(Wire.make_polygon([
        (-half,y0,z0-band_depth),(-half,y1,z1-band_depth),
        (-half,y1,z1+.01),(-half,y0,z0+.01)], close=True)), (2*half,0,0))
    outside = added-zone
    assert all(shape.is_valid for shape in (removed,added,outside))
    assert removed.volume < 1e-6 and outside.volume < 1e-6, (removed.volume,outside.volume)
    assert 0 < added.volume < 2*half*(y1-y0)*.075
    return {"removed_mm3": removed.volume, "added_mm3": added.volume,
            "added_outside_core_roof_mm3": outside.volume,
            "previous_normal_thickness_mm": P.arm_flange_thickness/(1+P.arm_rear_slope**2)**.5,
            "normal_thickness_mm": P.arm_flange_thickness,
            "vertical_inner_surface_shift_mm": P.rear_skin_vertical_offset-P.arm_flange_thickness,
            "previous_step_sha256": sha(V2/archive["snapshot"]/"cad/exported/replacement_finger.step")}


def dimension_checks(finger):
    from build123d import Edge
    from replacement_finger import P

    def chord(a, b):
        section = finger & Edge.make_line(a,b)
        lengths = [edge.length for edge in section.edges()]
        assert len(lengths) == 1, (a,b,lengths)
        return float(lengths[0])

    normal = np.array([0,-P.arm_rear_slope,1])/(1+P.arm_rear_slope**2)**.5
    rear = []
    for x in (-4,0,4):
        for y in (-52,-48,-42,-35,-29,-27):
            z = P.root_top_z+P.arm_rear_slope*(y-P.root_block_end_y)
            start = np.array((x,y,z))+normal*.01
            rear.append(chord(start,start-normal*5))
    front = [chord((0,y,11),(0,y,17)) for y in (-36,-35,-32)]
    webs = [chord((side*8,y,19),(side*15,y,19)) for side in (-1,1) for y in (-40,-35,-30)]
    roots = [chord((x+dx,P.mount_y-.1,z+dz),(x+dx,P.flange_front_y+.1,z+dz))
             for x in P.mount_hole_x for z in P.mount_hole_z
             for dx,dz in ((-1.6,0),(1.6,0),(0,-1.6),(0,1.6))]
    pads = [chord((x+np.sign(x)*1.4,y,8),(x+np.sign(x)*1.4,y,13)) for x,y in P.sensor_axes]
    lips = [chord((np.sign(x)*6.25,y,8),(np.sign(x)*6.25,y,13)) for x,y in P.sensor_axes]
    values = {"front_skin_min_mm": min(front), "rear_skin_normal_min_mm": min(rear),
              "main_web_min_mm": min(webs), "root_head_bearing_stack_min_mm": min(roots),
              "sensor_pad_stacks_mm": pads, "sensor_inner_lips_mm": lips,
              "service_side_material_mm": chord((9,-50,18),(15,-50,18)),
              "outer_sensor_rail_mm": chord((10,P.sensor_axes[-1][1],16),(15,P.sensor_axes[-1][1],16)),
              "inter_pocket_ligament_mm": min(np.diff(P.sensor_hole_y))-P.sensor_access_width,
              "bore_edge_ligament_mm": (P.sensor_pad_width-P.sensor_bore)/2,
              "distal_window_rim_mm": P.tip_y-P.window_y_max,
              "cable_saddle_vertical_mm": P.saddle_thickness,
              "tie_slot_mm": [P.tie_slot_width,P.tie_slot_length],
              "method": "B-rep line/solid intersections: 18 rear normal, 3 front, 6 web, 16 root and 12 pad/lip probes; nominal window/cable dimensions cross-checked against source"}
    assert min(front+rear) >= 3.5-1e-7 and min(webs) >= 5-1e-7 and min(roots) >= 6-1e-7
    assert np.allclose(pads,3.6) and np.allclose(lips,3.0)
    from build123d import import_step
    coupon = import_step(V2/"cad/exported/fastener_coupon.step")
    lands = coupon & Edge.make_line((-1,.65,1),(37,.65,1))
    values["coupon_identification_land_min_mm"] = min(edge.length for edge in lands.edges())
    assert values["coupon_identification_land_min_mm"] >= 1.6-1e-7
    return values


def slicer_discovery():
    names = ("bambu-studio","BambuStudio","bambustudio","orca-slicer","OrcaSlicer",
             "prusa-slicer","PrusaSlicer","slic3r","cura","CuraEngine")
    found = {name:shutil.which(name) for name in names if shutil.which(name)}
    home = Path.home()
    roots = [Path("/opt"),home/"Applications",home/"Downloads",home/".local/bin",
             home/".local/share/applications",home/".local/share/flatpak/app",
             Path("/var/lib/flatpak/app"),home/"workspace/deps",home/"workspace/envs"]
    matches = []
    for root in roots:
        if not root.exists():
            continue
        for parent, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in (".git","node_modules","__pycache__","site-packages")]
            for name in files:
                low = name.lower().replace("_", "-")
                if any(token in low for token in ("bambustudio","bambu-studio","orcaslicer","orca-slicer",
                                                    "prusaslicer","prusa-slicer","slic3r","curaengine")):
                    matches.append(str(Path(parent)/name))
    # Discovery never implies that an installation has been used or verified.
    return {"status":"NOT VERIFIED", "commands_checked":list(names), "commands_found":found,
            "application_paths_found":matches, "application_directories_searched":[str(p) for p in roots],
            "reason":"No compatible slicer executable/application found" if not found and not matches else
                     "Application candidate found; actual slicing and inspection are still required",
            "sliced":False, "slicer_project":None, "filament_g":None, "estimated_time_minutes":None}


def cad_build_screen(finger, write_image=True):
    """Selected 0.2 mm CAD sections only; deliberately NOT slicer verification."""
    from build123d import Plane, Pos
    from replacement_finger import P
    from PIL import Image, ImageDraw
    from render import font
    image = Image.new("RGB", (1440,1080), "#f5f7fa")
    draw = ImageDraw.Draw(image)
    draw.text((35,24),"CAD build-section screen — NOT a slicer preview",font=font(28),fill="#142c45")
    draw.text((35,69),"Side down: native X = -14 on bed. Sections 0.20 mm apart; no toolpaths or support generation.",font=font(18),fill="#46576b")
    panels, records = [], []
    for x in (5.9,9.1):
        plane = lambda xx: Plane(origin=(xx,0,0),x_dir=(0,1,0),z_dir=(1,0,0))
        current = finger & plane(x)
        previous = Pos(.2,0,0)*(finger & plane(x-.2))
        islands = []
        for face in current.faces():
            overlap = face & previous
            if overlap is None or overlap.area < 1e-7:
                islands.append(face)
        records.append({"native_x_mm":x,"print_height_mm":x+P.width/2,
                        "section_components":len(current.faces()),
                        "components_without_previous_section_overlap":[
                            {"area_mm2":f.area,"bounds_mm":[tuple(f.bounding_box().min),tuple(f.bounding_box().max)]}
                            for f in islands]})
        panels.append((x,current,previous,islands))
    for index,(x,current,previous,islands) in enumerate(panels):
        top = 125+index*420
        draw.text((35,top),f"Print Z={x+P.width/2:.1f} mm / native X={x:.1f} mm",font=font(23),fill="#142c45")
        scale, left, base = 11.3, 270, top+350
        def polygon(wire):
            n = max(24,int(np.ceil(wire.length/.12)))
            points = [wire.position_at(t) for t in np.linspace(0,1,n)]
            return [(left+(p.Y+70)*scale,base-(p.Z-4)*scale) for p in points]
        def paint(shape,color):
            for face in shape.faces():
                draw.polygon(polygon(face.outer_wire()),fill=color)
                for wire in face.inner_wires():
                    draw.polygon(polygon(wire),fill="#f5f7fa")
        paint(current,"#9fc4e5")
        difference = current-previous
        paint(difference,"#e6a64d")
        for face in islands:
            paint(face,"#d96257")
        for face in previous.faces():
            for wire in face.wires():
                draw.line(polygon(wire),fill="#365069",width=1)
        label = "Three pad lips begin without material directly below. Accessible supports need slicer review." if islands else "Core / web closure: orange material is new at this section; bridge paths need slicer review."
        draw.text((35,top+370),label,font=font(18),fill="#46576b")
    draw.text((35,982),"Blue: current material   Orange: newly appearing material   Red: no previous-section overlap   Line: previous section",font=font(18),fill="#142c45")
    draw.text((35,1026),"CAD is one connected solid. Local unsupported starts do not become printable until support/bridge toolpaths are verified.",font=font(17),fill="#46576b")
    path = V2/"drawings/printability_sections.png"
    if write_image:
        image.save(path)
    screens = {}
    for path in sorted((V2/"cad/exported").glob("*_print.stl")):
        mesh = trimesh.load_mesh(path)
        mask = (mesh.face_normals[:,2] < -np.cos(np.deg2rad(45))-1e-8) & (mesh.triangles[:,:,2].max(axis=1)>1e-5)
        screens[path.name] = {"downward_area_beyond_45_degrees_mm2":float(mesh.area_faces[mask].sum()),
                              "flagged_facets":int(mask.sum()), "bounds_mm":mesh.bounds.tolist()}
    return {"status":"CAD screening only; NOT VERIFIED in a slicer", "selected_sections":records,
            "overhang_screen":screens, "core_nominal_vertical_gap_upper_bound_mm":
                P.root_top_z-P.rear_skin_vertical_offset-P.arm_front_z-P.arm_flange_thickness,
            "bridge_limit_screen_mm":10, "drawing":"drawings/printability_sections.png",
            "drawing_sha256":sha(V2/"drawings/printability_sections.png")}


def audit_printability(validation=None):
    from build123d import import_step
    from replacement_finger import P, make_finger
    manifest = V2/"docs/build-manifest.json"
    if validation is None:
        validation = json.loads((V2/"docs/validation.json").read_text())
    assert validation["status"] == "passed"
    assert validation["build_manifest_sha256"] == sha(manifest)
    build = json.loads(manifest.read_text())
    for group in ("source_sha256","artifact_sha256"):
        for name,digest in build[group].items():
            assert sha(V2/name) == digest, f"Stale CAD or audit source: {name}"
    fixtures = check_intersection_kernel()
    mesh_paths = sorted((V2/"cad/exported").glob("*.stl"))
    assert len(mesh_paths) == 6
    meshes = {path.name:audit_mesh(path) for path in mesh_paths}
    finger = import_step(V2/"cad/exported/replacement_finger.step")
    dimensions = dimension_checks(finger)
    source = make_finger()
    # Coincident imported trims can produce an invalid direct STEP/STEP cut.
    # Prove export/source equality in both directions, then use the source
    # against the archive; never accept the volume of an invalid boolean result.
    export_minus_source, source_minus_export = finger-source, source-finger
    assert all(s.is_valid and s.volume < 1e-6 for s in (export_minus_source,source_minus_export))
    skin = check_skin_correction(source)
    skin["current_STEP_minus_source_mm3"] = export_minus_source.volume
    skin["source_minus_current_STEP_mm3"] = source_minus_export.volume
    skin["comparison_method"] = "Archived STEP versus parametric source, with two valid zero-volume cuts proving current STEP/source equality. Invalid direct imported-STEP/imported-STEP boolean results are not accepted."
    screen = cad_build_screen(finger, write_image=False)
    slicing = slicer_discovery()
    access = json.loads((V2/"docs/sensor-screw-access.json").read_text())
    assert access["status"] == "reference_geometry_passed_actual_hardware_unverified"
    mesh_ok = all(row["result"] == "PASS" for row in meshes.values())
    checks = [
        {"check":"Mesh integrity","result":"PASS" if mesh_ok else "FAIL",
         "evidence":"All 6 current STLs: single closed manifold surface, consistent winding, no degenerate/duplicate faces or improper triangle intersections; exact file hashes recorded."},
        {"check":"Minimum dimensions","result":"PASS",
         "evidence":"Measured 3.500 mm normal skins, 5.000 mm main webs, 6.000 mm root seats. Sensor/service interface exceptions listed below; coupon identification lands increased to 1.6 mm."},
        {"check":"Overhangs and bridging","result":"NOT VERIFIED",
         "evidence":"No slicer. CAD flags three unsupported pad starts near build Z19.9 and a nominal core gap up to 11.926 mm; actual bridge paths remain unknown."},
        {"check":"Support accessibility","result":"NOT VERIFIED",
         "evidence":"Open sensor window provides potential access to pad supports. No generated support geometry or layer review; internal-core support removal is not established."},
        {"check":"Mounting and sensor compatibility","result":"PASS",
         "evidence":"Reference CAD: unchanged PiPER axes, 17.5 x 8 sensor pattern, sensor plane/reach and cable route; S1-S6 insertion/seat/tool/removal PASS. Actual hardware and plug latch fit remain unverified."},
        {"check":"Structural orientation","result":"PASS",
         "evidence":"Finger X=-14 side down: longitudinal Y and dominant Y-Z grip bending remain in the layer plane, including the root. No quantified printed strength claim; lateral/torsional loading is unvalidated."},
        {"check":"PETG slicing","result":"NOT VERIFIED","evidence":slicing["reason"]+"; no toolpath, filament/time estimate or slicer-native project."}]
    exceptions = [
        "4.0 mm local side walls at the R3 root service opening preserve screw/key and cable access; the main webs stay 5 mm and all root bearing stacks stay 6 mm.",
        "Sensor interface: 3.6 mm stacks, 3.0 mm lips/outer rails, 3.50026 mm inter-pocket ligaments and 1.95 mm bore-edge ligaments. Short lips clear electronics and preserve direct screw access; intentional interface exception to main-web/skin dimensions.",
        "The existing distal sensor-window rim is 1.5 mm along Y. It preserves the sensor opening and holder tip boundary; outside the root/arm load path and not a screw-head bearing seat. Recorded interface exception to the 1.6 mm detail target.",
        "The 3 mm curved cable saddle and 1.6 x 3.6 mm tie slots retain the established cable clearance. Saddle dimension is vertical, not a new main-skin specification.",
        "The 0.15 mm bore-mouth chamfer and R0.4 pocket-floor transitions are interface reliefs, not isolated thin walls; both are retained for head seating. Coupon 1 mm identification cuts are voids; solid lands are now >=1.6 mm."]
    report = {"date":"2026-10-16","units":"mm","validation_level":"CAD VALIDATED" if mesh_ok else "NOT VALIDATED",
        "print_ready":False,"physical_validation":False,"full_print_release":False,
        "scope":"Six active STL files = three printable components in native and print placements. Imported vendor meshes, assembly visualization meshes and historical revisions are not current printable exports.",
        "build_manifest_sha256":sha(manifest),"baseline":{"printer":"Bambu Lab P2S","material":"PETG",
            "nozzle_mm":.4,"layer_mm":.2,"wall_loops":[4,5],"infill_percent":[25,35],
            "status":"User evaluation baseline; no actual filament/printer process profile or toolpaths generated"},
        "mesh_method":"Exhaustive AABB sweep, plane clipping and coplanar triangle contacts, allowing only indexed shared-edge/vertex contact; independent edge incidence and vertex-link manifold checks. No repair applied.",
        "intersection_kernel_cases_passed":fixtures,"meshes":meshes,"dimensions":dimensions,
        "interface_exceptions":exceptions,"rear_skin_correction":skin,"cad_build_screen":screen,
        "slicing":slicing,"checks":checks,
        "orientations":{"replacement_finger":"Existing print STL: native X=-14 on bed; footprint 27 x 73.2, height 28. Dominant bending in layer plane.",
            "mount_fit_gauge":"Native Y=-70 mating face on bed; footprint 28 x 22.5, height 6; all bores vertical. An unpowered fit gauge, not a load-bearing finger.",
            "fastener_coupon":"Flat XY base on bed; 36 x 18, height 3.6; all fit holes and identification cuts vertical. An unpowered fit coupon."},
        "limits":["CAD VALIDATED applies to the supplied/reference geometry; actual screws, driver details, tapped usable depth, torque, PETG error and physical fit remain unverified.",
                  "Complete printed-layer continuity and opening retention are NOT VERIFIED; the CAD section screen is not a slicer.",
                  "Actual stepped plug withdrawal/latch geometry remains unresolved: the conservative plug box clips vendor housing, although printed-holder clearance passes.",
                  "Existing ideal fully-solid beam estimates and density-derived mass are not predictions for 4-5 walls / 25-35% infill, and are not slicer filament/time estimates.",
                  "Existing PRINT-HOLD.md remains unchanged; no full-print release or robot command."]}
    (V2/"docs/printability-acceptance.json").write_text(json.dumps(report,indent=2)+"\n")
    rows = "\n".join(f"| {r['check']} | **{r['result']}** | {r['evidence']} |" for r in checks)
    mesh_rows = "\n".join(f"| `{name}` | {r['facets']} | {r['surface_components']} | {r['improper_triangle_intersections']} | {r['result']} |" for name,r in meshes.items())
    text = f"""# V2 PETG / P2S acceptance — 2026-10-16

**{report['validation_level']} for the reference geometry. Not SLICE VERIFIED, not PHYSICALLY VALIDATED, not print-ready.**

Baseline: PETG, 0.4 mm nozzle, 0.20 mm layers, 4–5 walls, 25–35% infill. These are evaluation settings, not a tested process. [Machine evidence](printability-acceptance.json) records exact STL hashes and the build manifest; [assembly evidence](validation.json) and the [six-screw audit](sensor-screw-access.md) supply the CAD checks.

| Check | Result | Evidence |
| --- | --- | --- |
{rows}

## Mesh evidence

{report['scope']} All six were checked individually, without mesh repair. Every edge has exactly two incident faces and every vertex has a single manifold fan. Finite coordinates, positive volume, consistent winding, single surface, duplicate and zero-area faces were checked. Triangle intersections were checked explicitly, including coplanar overlaps; legitimate common-edge/vertex contact is excluded. Numerical contact tolerance is 0.000001 mm; plane zero tolerance is 0.0000000001 mm. Nine analytic crossing/contact/separation cases passed. These are mesh checks, not a guarantee that slicing retains every hole.

| STL | Triangles | Connected surfaces | Improper intersections | Result |
| --- | ---: | ---: | ---: | --- |
{mesh_rows}

## Dimensions and focused corrections

The rear skin measured **3.427783 mm normal to its slope** despite a 3.5 mm vertical setting. Moving only the inner core roof down **{skin['vertical_inner_surface_shift_mm']:.6f} mm** yields **3.500 mm normal thickness**, adding **{skin['added_mm3']:.3f} mm³** and removing no finger material. Exact old/new booleans confine the addition to the existing core roof and R2 transitions. Outer geometry, root mounting, sensor alignment and cable route are fixed. Eight affected source/export files are preserved in [the immediate prior geometry snapshot](pre-printability-revision.json); all earlier complete snapshots and V1 are unchanged.

The CAD kernel returned an invalid direct cut between two STEP imports. That result is rejected. The accepted comparison uses the archived STEP against the parametric solid, plus valid cuts in both directions between the current STEP and its source showing **zero geometric difference**. Thickness is measured on the reimported STEP and meshes are independently checked; no numerical or printing clearance was added to bypass the comparison.

The front skin measures **{dimensions['front_skin_min_mm']:.3f} mm**, main webs **{dimensions['main_web_min_mm']:.3f} mm**, and all four root bearing stacks **{dimensions['root_head_bearing_stack_min_mm']:.3f} mm**. Coupon identification-notch spacing now leaves **{dimensions['coupon_identification_land_min_mm']:.3f} mm** solid lands instead of 1 mm projections; its hole positions, diameters and 3.6 mm test stack are unchanged. The measured probes and their method are in the JSON.

The interface-specific exceptions are:

"""+"\n".join(f"- {item}" for item in exceptions)+f"""

All six sensor seats remain Z=12.8 above the fixed Z=9.2 sensor plane: **3.6 mm pass-through**, no counterbore, candidate **M1.6×5, pitch 0.35, head Ø3 × 1.6, hex 1.5**. Nominal thread penetration is 1.4 mm into the specified maximum 2 mm depth. Reference driver clearance is **0.75 mm radial**, or **0.60 mm** under the stated 0.30 mm diametric undersize sensitivity. Actual screw/tool dimensions, full usable threads, print tolerance and torque remain UNVERIFIED for every screw. No new clearance compensation was added.

## Orientation and outstanding slicing evidence

"""+"\n".join(f"- **{name}:** {description}" for name,description in report['orientations'].items())+"""

The finger orientation keeps longitudinal material and dominant gripping-plane bending within layers through the root. It avoids placing the entire root in interlayer tension from the main bending load. Lateral/torsional loads and local joints still need physical validation. Existing fillets and load paths are retained; no infill-derived strength rating is assigned.

![Selected CAD sections, not slicer layers](../drawings/printability_sections.png)

The selected 0.20 mm CAD sections expose three positive-X pad lips beginning near print Z=19.9 mm without overlap with the preceding section. They need support from the accessible central window or a validated toolpath strategy. Their native X-facing sides are candidate support-contact surfaces; the sensor plane, head seats and root datum must remain free of support contact. The main part is still one connected solid; these are local build-start risks, not disconnected STL bodies.

The core's nominal vertical gap reaches **11.926 mm**, above the conservative 10 mm bridge screen; R2 corners reduce closure spans, but actual bridge direction, anchoring and extrusion are not verified. The enclosed core communicates with the root service opening, but removal of generated internal support has not been demonstrated. Do not assume dense internal supports are removable. The open pockets, horizontal holes, tie slots, core closure and root require layer inspection. The flat gauge and coupon have vertical holes and no >45° downward faces above the bed in the mesh screen, but are also unsliced.

No compatible slicer was found in PATH or the application/workspace locations recorded in the JSON. **Slicer project, print time, filament usage, generated supports and retention of holes after slicing: NOT VERIFIED / unavailable.** CAD sections do not replace these results. The user baseline supersedes the earlier eight-wall/100% process suggestion. Solid-beam comparisons remain geometric comparisons; their mass and stiffness must not be presented as predictions for this sparse-infill baseline.

The [existing print hold](../../PRINT-HOLD.md) and [physical checklist](../measurements/fit-checklist.md) remain in force. No printing, physical assembly or powered motion was performed.
"""
    (V2/"docs/printability-acceptance.md").write_text(text)
    assert mesh_ok, "STL integrity failed; inspect printability-acceptance.json"
    print("Printability: CAD VALIDATED for reference geometry; slicing NOT VERIFIED; not print-ready",flush=True)
    return report


if __name__ == "__main__":
    audit_printability()
