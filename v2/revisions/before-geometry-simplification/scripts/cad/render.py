"""Small orthographic, depth-buffered CAD renderer; all inputs in millimetres."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def render(meshes, path, direction, title, subtitle="", labels=(), up_axis=(0, 0, 1)):
    width, height = 1440, 1080
    view = np.asarray(direction, dtype=float)
    view /= np.linalg.norm(view)
    up_axis = np.asarray(up_axis, dtype=float)
    if abs(view @ up_axis) > 0.99:
        up_axis = np.array((0, 1, 0))
    right = np.cross(up_axis, view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    points = np.vstack([m.vertices for m in meshes.values()])
    screen = np.column_stack((points @ right, points @ up))
    span = np.ptp(screen, axis=0)
    scale = min((width - 220) / max(span[0], 1), (height - 230) / max(span[1], 1))
    center = (screen.min(0) + screen.max(0)) / 2

    def project(vertices):
        xy = (np.column_stack((vertices @ right, vertices @ up)) - center) * scale
        xy[:, 0] += width / 2
        xy[:, 1] = height / 2 + 15 - xy[:, 1]
        return xy

    pixels = np.full((height, width, 3), (245, 247, 250), dtype=np.uint8)
    zbuffer = np.full((height, width), -np.inf)
    light = (view + up * 0.8 - right * 0.5)
    light /= np.linalg.norm(light)
    for mesh in meshes.values():
        xy, depth = project(mesh.vertices), mesh.vertices @ view
        normals = mesh.face_normals
        colors = mesh.visual.face_colors[:, :3].astype(float)
        for i in np.flatnonzero(normals @ view > 1e-9):
            face = mesh.faces[i]
            triangle = xy[face]
            xmin, ymin = np.maximum(np.floor(triangle.min(0)).astype(int), 0)
            xmax, ymax = np.minimum(np.ceil(triangle.max(0)).astype(int), (width - 1, height - 1))
            if xmax < xmin or ymax < ymin:
                continue
            a, b, c = triangle
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-10:
                continue
            xx, yy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            wa = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
            wb = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
            wc = 1 - wa - wb
            zz = wa * depth[face[0]] + wb * depth[face[1]] + wc * depth[face[2]]
            patch = zbuffer[ymin:ymax + 1, xmin:xmax + 1]
            visible = (wa >= -1e-8) & (wb >= -1e-8) & (wc >= -1e-8) & (zz > patch)
            patch[visible] = zz[visible]
            shade = 0.43 + 0.57 * max(0, normals[i] @ light)
            pixels[ymin:ymax + 1, xmin:xmax + 1][visible] = np.clip(colors[i] * shade, 0, 255).astype(np.uint8)
    image = Image.fromarray(pixels)
    draw = ImageDraw.Draw(image)
    draw.text((32, 23), title, font=font(29), fill="#142c45")
    draw.text((32, 68), subtitle, font=font(18), fill="#46576b")
    for point, text, offset in labels:
        x, y = project(np.array([point]))[0]
        tx, ty = x + offset[0], y + offset[1]
        draw.line((x, y, tx, ty), fill="#526477", width=2)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#526477")
        box = draw.textbbox((tx, ty), text, font=font(19))
        draw.rectangle((box[0] - 5, box[1] - 4, box[2] + 5, box[3] + 4), fill="#f5f7fa")
        draw.text((tx, ty), text, font=font(19), fill="#142c45")
    draw.text((32, height - 40), "V2 / direct replacement   |   CAD review only; physical fit and cable checks pending", font=font(18), fill="#46576b")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
