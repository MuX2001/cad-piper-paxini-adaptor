"""Read-only supplier imports and source-derived measurements. No V1 imports."""

from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh
from build123d import Face, Shell, Solid, Wire, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_SurfaceOfExtrusion, GeomAbs_Plane

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "v2"
GRIPPER = ROOT / "assets/vendor_files/agx_arm_urdf-main/agx_gripper"
SENSOR = next((ROOT / "assets/vendor_files/GEN3触觉传感器3D模型").rglob("*M2324*.stp"))


def vendor_mesh(name):
    mesh = trimesh.load_mesh(GRIPPER / "meshes" / f"{name}.stl", process=True)
    mesh.apply_scale(1000)  # URDF metres -> internal mm. Original never rewritten.
    return mesh


def carrier_and_finger(side):
    mesh = vendor_mesh(f"gripper_link{side}")
    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), min_len=1, engine="scipy")
    # Select a complete disconnected body, never slice a moving mechanism.
    candidates = [c for c in components
                  if np.allclose(mesh.vertices[mesh.faces[c]].min(axis=(0, 1)), (-8.5, -76.5, 4), atol=.001)
                  and np.allclose(mesh.vertices[mesh.faces[c]].max(axis=(0, 1)), (8.5, -70, 26.5), atol=.001)]
    assert len(candidates) == 1, "Supplied carrier no longer matches known body; reinspect"
    indices = candidates[0]
    carrier = mesh.submesh([indices], append=True, repair=False)
    finger = mesh.submesh([np.setdiff1d(np.arange(len(mesh.faces)), indices)], append=True, repair=False)
    assert carrier.is_watertight and carrier.is_winding_consistent
    return carrier, finger


def mating_holes(mesh):
    """Fit circles to boundary loops of the actual carrier front plane."""
    triangles = mesh.triangles
    front = np.all(np.abs(triangles[:, :, 1] + 70) < 1e-4, axis=1) & (mesh.face_normals[:, 1] > .99)
    faces = mesh.faces[front]
    edges = np.sort(np.vstack((faces[:, :2], faces[:, 1:], faces[:, [2, 0]])), axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    boundary = unique[counts == 1]
    loops = trimesh.graph.connected_components(boundary, nodes=np.unique(boundary), min_len=3, engine="scipy")
    result = []
    for loop in loops:
        pts = mesh.vertices[loop][:, [0, 2]]
        if np.ptp(pts, axis=0).max() > 5:
            continue  # outer rectangular perimeter
        solution = np.linalg.lstsq(np.c_[2 * pts, np.ones(len(pts))], (pts**2).sum(1), rcond=None)[0]
        center = solution[:2]
        radius = np.sqrt(solution[2] + center @ center)
        residual = np.abs(np.linalg.norm(pts - center, axis=1) - radius).max()
        result.append({"x": float(center[0]), "z": float(center[1]), "radius": float(radius),
                       "max_fit_residual_mm": float(residual), "vertices": len(pts)})
    return sorted(result, key=lambda row: (round(row["x"], 3), round(row["z"], 3)))


@lru_cache
def sensor_native():
    return import_step(SENSOR)


def sensor_mounting_axes():
    axes = set()
    for face in sensor_native().faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() == GeomAbs_Cylinder and abs(surface.Cylinder().Radius() - .625) < 1e-5:
            axis = surface.Cylinder().Axis()
            assert abs(axis.Direction().Z()) > .999
            axes.add(tuple(round(x, 8) for x in axis.Location().Coord()[:2]))
    return sorted(axes)


def reach_measurements():
    """Functional reach: stock distal contact plane and broad tactile crown."""
    stock = []
    for side in (1, 2):
        carrier, finger = carrier_and_finger(side)
        mask = (finger.face_normals[:, 2] < -.99) & (np.abs(finger.triangles[:, :, 2]).max(1) < .0001)
        points = finger.triangles[mask].reshape(-1, 3)
        area = finger.area_faces[mask]
        center = (finger.triangles_center[mask] * area[:, None]).sum(0) / area.sum()
        stock.append({"side": side, "mount_y_mm": float(carrier.bounds[1, 1]),
                      "tip_y_mm": float(finger.bounds[1, 1]),
                      "reach_mm": float(finger.bounds[1, 1] - carrier.bounds[1, 1]),
                      "contact_y_mm": [float(points[:, 1].min()), float(points[:, 1].max())],
                      "contact_centroid_y_mm": float(center[1]), "contact_area_mm2": float(area.sum())})
    crown = [f for f in sensor_native().faces()
             if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_SurfaceOfExtrusion
             and f.area > 50 and f.bounding_box().min.Z > 5 and f.normal_at().Z > .98]
    assert len(crown) == 3, "Reinspect tactile crown if supplier model changes"
    return {"stock": stock, "sensor_crown_native_y_mm":
            [min(f.bounding_box().min.Y for f in crown), max(f.bounding_box().max.Y for f in crown)],
            "sensor_crown_faces": 3, "sensor_crown_area_mm2": sum(f.area for f in crown),
            "crown_definition": "Three broad near-+Z extrusion faces, excluding perimeter bevels and housing"}


def connector_measurements():
    """Recover the paired proximal receptacle mouths, not a guessed rear normal."""
    result = []
    for f in sensor_native().faces():
        b = f.bounding_box()
        if (BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_Plane
                and abs(f.area - 2.641) < .001 and f.normal_at().Y > .999
                and b.max.Z < .251 and b.min.Z < -1):
            result.append({"mouth_x_mm": (b.min.X + b.max.X) / 2,
                           "mouth_y_mm": b.max.Y, "body_z_mm": [b.min.Z, b.max.Z],
                           "exit_native": [0, 1, 0], "exit_jaw": [0, -1, 0]})
    assert len(result) == 2
    return sorted(result, key=lambda p: p["mouth_x_mm"])


def cad_mesh(shape, color=(43, 123, 194, 255)):
    vertices, faces = shape.tessellate(.04, .15)
    mesh = trimesh.Trimesh(vertices=[tuple(v) for v in vertices], faces=faces, process=True)
    mesh.visual.face_colors = color
    return mesh


def faceted_solid(mesh):
    """Exact triangles of the retained carrier, sewn as a STEP reference solid."""
    faces = [Face(Wire.make_polygon(triangle.tolist(), close=True)) for triangle in mesh.triangles]
    solid = Solid(Shell(faces))
    assert solid.is_valid and abs(solid.volume - mesh.volume) < .01
    return solid


def jaw_matrix(side, opening):
    if side not in (1, 2) or not 0 <= opening <= 100:
        raise ValueError("side 1/2 and total commanded opening 0..100 mm required")
    sign = 1 if side == 1 else -1
    # Exact quarter/half turns avoid URDF's rounded pi values.
    return np.array([[sign, 0, 0, 0], [0, 0, -sign, -sign * opening / 2],
                     [0, 1, 0, 138], [0, 0, 0, 1]], dtype=float)
