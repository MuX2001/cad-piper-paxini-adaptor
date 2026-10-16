"""One-piece ribbed direct replacement; two identical parts, opposed by URDF pose."""

from math import sqrt, pi

from build123d import Box, Edge, Face, Plane, Pos, Rot, Solid, Wire

from v2_parameters import P
from references import sensor_native


def box_between(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def bore(origin, axis, diameter, length):
    return Solid.make_cylinder(diameter / 2, length, Plane(origin=origin, z_dir=axis))


def make_flange(p=P):
    part = box_between(-p.width / 2, p.width / 2, p.mount_y, p.flange_front_y,
                       p.carrier_z_min, p.carrier_z_max)
    for x in p.mount_hole_x:
        for z in p.mount_hole_z:
            part -= bore((x, p.mount_y - 1, z), (0, 1, 0), p.mount_bore, p.flange_thickness + 2)
    # Preserve access to the existing central linkage feature; never modify it.
    part -= bore((0, p.mount_y - 1, p.linkage_access_z), (0, 1, 0),
                 p.linkage_access_diameter, p.flange_thickness + 2)
    return part


def make_finger(p=P):
    p.check()
    part = make_flange(p)
    rails = box_between(-p.width / 2, p.width / 2, p.sensor_frame_proximal_y, p.tip_y,
                        p.sensor_rear_z, p.rail_back_z)
    rails -= box_between(-p.window_half_width, p.window_half_width,
                         p.window_y_min, p.window_y_max, p.sensor_rear_z - 1, p.rail_back_z + 1)
    part += rails
    for x0 in (-p.width / 2, p.width / 2 - p.arm_flange_width):
        part += box_between(x0, x0 + p.arm_flange_width, p.flange_front_y,
                            p.sensor_frame_proximal_y, p.arm_front_z,
                            p.arm_front_z + p.arm_flange_thickness)
    for x0 in (-p.width / 2, p.width / 2 - p.rib_thickness):
        rib = Face(Wire.make_polygon([
            (x0, p.flange_front_y, p.arm_front_z),
            (x0, p.flange_front_y, p.carrier_z_max),
            (x0, p.sensor_frame_proximal_y, p.arm_distal_top_z),
            (x0, p.tip_y, p.rail_back_z),
            (x0, p.sensor_frame_proximal_y, p.rail_back_z),
            (x0, p.sensor_frame_proximal_y, p.arm_front_z)], close=True))
        part += Solid.extrude(rib, (p.rib_thickness, 0, 0))
    # Curved, open saddle doubles as a mid-span cross brace. No cover traps
    # the leads; a removable tie restrains the harness well away from its plug.
    sections = []
    for i in range(9):
        y = p.saddle_y_min + i * (p.saddle_y_max - p.saddle_y_min) / 8
        run = p.bend_start_y - y
        cos_angle = sqrt(1 - (run / p.cable_bend_radius)**2)
        z = p.cable_z + p.cable_bend_radius * (1 - cos_angle)
        top = z - p.cable_thickness / (2 * cos_angle) - p.saddle_cable_clearance
        sections.append(Wire.make_polygon([(-p.width/2, y, top-p.saddle_thickness),
            (p.width/2, y, top-p.saddle_thickness), (p.width/2, y, top), (-p.width/2, y, top)], close=True))
    saddle = Solid.make_loft(sections, ruled=True)
    part += saddle
    for x0 in (-p.width/2, p.width/2-p.rib_thickness):
        part += box_between(x0, x0+p.rib_thickness, p.saddle_y_min, p.saddle_y_max,
                            saddle.bounding_box().min.Z, p.arm_front_z+1)
    for x, y in p.sensor_axes:
        part -= bore((x, y, p.sensor_rear_z - 1), (0, 0, 1), p.sensor_bore, p.rail_thickness + 2)
        part -= bore((x, y, p.sensor_screw_seat_z), (0, 0, 1), p.sensor_head_pocket, 30)
    for x in p.mount_hole_x:
        for z in p.mount_hole_z:
            part -= bore((x, p.flange_front_y, z), (0, 1, 0), p.mount_head_pocket,
                         p.mount_head_height + .3)
            part -= bore((x, p.flange_front_y + p.mount_head_height, z), (0, 1, 0),
                         p.mount_driver_diameter, p.tip_y - p.flange_front_y + 2)
    for x in p.tie_slot_x:
        part -= box_between(x-p.tie_slot_width/2, x+p.tie_slot_width/2,
                            p.tie_y-p.tie_slot_length/2, p.tie_y+p.tie_slot_length/2, 0, 35)
    part.label = "V2 replacement finger (print 2; physical fit pending)"
    assert part.is_valid and len(part.solids()) == 1
    return part


def placed_sensor(p=P):
    return Pos(0, p.sensor_y_translation, p.sensor_z_translation) * Rot(180, 0, 0) * sensor_native()


def jaw_location(side, opening):
    if side not in (1, 2) or not 0 <= opening <= 100:
        raise ValueError("Invalid jaw pose")
    return Pos(0, (-1 if side == 1 else 1) * opening / 2, 138) * Rot(0, 0, 0 if side == 1 else 180) * Rot(90, 0, 0)


def print_location(p=P):
    # Put the planar X=-width/2 side on the bed. Y/Z load paths lie in layers.
    return Pos(0, -p.mount_y, p.width / 2) * Rot(0, -90, 0)


def hardware(p=P):
    """Unthreaded candidate screw envelopes; threads/heads must be measured."""
    screws = {}
    for i, (x, z) in enumerate((x, z) for x in p.mount_hole_x for z in p.mount_hole_z):
        shaft = bore((x, p.flange_front_y - p.mount_screw_length, z), (0, 1, 0),
                     p.mount_screw_diameter, p.mount_screw_length)
        head = bore((x, p.flange_front_y, z), (0, 1, 0), p.mount_head_diameter, p.mount_head_height)
        screws[f"mount_screw_{i + 1}_assumed_M2x6"] = shaft + head
    for i, (x, y) in enumerate(p.sensor_axes):
        shaft = bore((x, y, p.sensor_screw_seat_z - p.sensor_screw_length), (0, 0, 1),
                     1.6, p.sensor_screw_length)
        head = bore((x, y, p.sensor_screw_seat_z), (0, 0, 1), 3.0, p.sensor_head_height)
        screws[f"sensor_screw_{i + 1}_M1p6x4"] = shaft + head
    return screws


def plug_envelope(p=P):
    """Only the exposed portion of the horizontal catalog plug, not a rear block."""
    return box_between(p.plug_center_x - p.plug_width / 2, p.plug_center_x + p.plug_width / 2,
                       p.cable_start_y, p.plug_mouth_y,
                       p.sensor_z_translation - p.plug_native_z_min - p.plug_height,
                       p.sensor_z_translation - p.plug_native_z_min)


def moving_cable_path(p=P):
    x, y, z, r = p.plug_center_x, p.bend_start_y, p.cable_z, p.cable_bend_radius
    start, first = (x, p.cable_start_y, z), (x, y, z)
    middle = (x, y-r/sqrt(2), z+r*(1-1/sqrt(2)))
    last = (x, y-r, z+r)
    return Wire([Edge.make_line(start, first), Edge.make_three_point_arc(first, middle, last)])


def ribbon_section(x, y, z, p=P):
    return Wire.make_polygon([(x-p.cable_width/2, y, z-p.cable_thickness/2),
        (x+p.cable_width/2, y, z-p.cable_thickness/2),
        (x+p.cable_width/2, y, z+p.cable_thickness/2),
        (x-p.cable_width/2, y, z+p.cable_thickness/2)], close=True)


def cable_envelope(p=P):
    """Loose-lead clearance envelope: 12 mm straight parallel exit, then R38."""
    return Solid.sweep(ribbon_section(p.plug_center_x, p.cable_start_y, p.cable_z, p), moving_cable_path(p))


def service_cable_path(opening, p=P):
    """Base-frame jaw-1 traveling loop: same length at every jaw opening."""
    if not 0 <= opening <= 100:
        raise ValueError("opening must be 0..100 mm")
    z = 138 + p.bend_start_y - p.cable_bend_radius
    u = p.loop_turn_u_closed + opening / 4
    a = (p.plug_center_x, -(p.cable_z+p.cable_bend_radius+opening/2), z)
    b = (p.plug_center_x, -u, z)
    c = (p.fixed_loom_x, -u, z)
    d = (p.fixed_loom_x, -p.fixed_turn_radius, z)
    e = (p.fixed_loom_x, 0, z-p.fixed_turn_radius)
    mid = ((p.plug_center_x+p.fixed_loom_x)/2, -u-p.loop_radius, z)
    end_mid = (p.fixed_loom_x, -p.fixed_turn_radius+p.fixed_turn_radius/sqrt(2),
               z-p.fixed_turn_radius+p.fixed_turn_radius/sqrt(2))
    return Wire([Edge.make_line(a,b), Edge.make_three_point_arc(b,mid,c),
                 Edge.make_line(c,d), Edge.make_three_point_arc(d,end_mid,e)])


def service_cable(side, opening, p=P):
    path = service_cable_path(opening, p)
    start = path.position_at(0)
    shape = Solid.sweep(ribbon_section(start.X,start.Y,start.Z,p),path)
    return shape if side == 1 else Rot(0,0,180)*shape


def strain_relief_band(p=P):
    """Loose display envelope of a releasable 2.5 mm tie, not a printed part."""
    a,b = p.tie_slot_x
    outer = box_between(a-.4,b+.4,p.tie_y-1.25,p.tie_y+1.25,3.7,12.0)
    return outer - box_between(a+.4,b-.4,p.tie_y-2,p.tie_y+2,4.5,11.2)


def make_coupon(p=P):
    """Unpowered fit coupon: 3 lanes, nominal / +0.1 / +0.2 mm diameters."""
    part = box_between(0, 36, 0, 18, 0, 4)
    for i, offset in enumerate((0, .1, .2)):
        x = 6 + 12 * i
        part -= bore((x, 5, -1), (0, 0, 1), p.mount_bore + offset, 6)
        part -= bore((x, 13, -1), (0, 0, 1), p.sensor_bore + offset, 6)
        part -= bore((x, 13, 4 - p.sensor_head_recess), (0, 0, 1), p.sensor_head_pocket + offset, 3)
        # Edge notches identify lanes without tiny embossed text.
        for j in range(i + 1):
            part -= box_between(x - 2 + 2 * j, x - 1 + 2 * j, -.1, 1.3, -1, 5)
    part.label = "V2 fastener fit coupon; lanes 1/2/3 = +0/+0.1/+0.2 mm"
    return part
