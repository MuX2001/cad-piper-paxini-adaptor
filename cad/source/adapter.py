"""Parametric two-piece, bolted clamp for the unmodified Piper jaw."""

from build123d import Box, Cylinder, Face, Pos, RegularPolygon, Rot, Solid, Wire, extrude

from parameters import ClampParameters, M2324Reference


def _section(y: float, half_width: float, bottom: float, top: float) -> Wire:
    return Wire.make_polygon(
        [
            (-half_width, y, bottom),
            (half_width, y, bottom),
            (half_width, y, top),
            (-half_width, y, top),
        ]
    )


def _cylinder(x: float, y: float, z: float, radius: float, height: float):
    return Pos(x, y, z) * Cylinder(radius, height)


def make_adapter(
    clamp: ClampParameters = ClampParameters(),
    sensor: M2324Reference = M2324Reference(),
):
    """Return (inner_plate, outer_roof) in millimetre jaw-local coordinates."""

    outer = Solid.make_loft(
        [
            _section(
                clamp.proximal_y,
                clamp.cavity_half_width(clamp.proximal_y) + clamp.side_wall,
                clamp.plate_bottom,
                clamp.cavity_top(clamp.proximal_y) + clamp.roof_wall,
            ),
            _section(
                clamp.distal_y,
                clamp.cavity_half_width(clamp.distal_y) + clamp.side_wall,
                clamp.plate_bottom,
                clamp.cavity_top(clamp.distal_y) + clamp.roof_wall,
            ),
        ],
        ruled=True,
    )
    cavity = Solid.make_loft(
        [
            _section(
                clamp.cavity_proximal_y,
                clamp.cavity_half_width_proximal,
                clamp.cavity_bottom,
                clamp.cavity_top_proximal,
            ),
            _section(
                clamp.cavity_distal_y,
                clamp.cavity_half_width_distal,
                clamp.cavity_bottom,
                clamp.cavity_top_distal,
            ),
        ],
        ruled=True,
    )
    shell = outer - cavity

    # Saw-free virtual split. V2 roof prints distal-end-down; see print guide.
    lower_clip = Pos(0, 0, clamp.split_z - 50) * Box(150, 150, 100)
    upper_clip = Pos(0, 0, clamp.split_z + 50) * Box(150, 150, 100)
    inner_plate = shell & lower_clip
    outer_roof = shell & upper_clip

    for x, y in sensor.hole_positions_in_jaw:
        inner_plate -= _cylinder(x, y, -1.9, (clamp.sensor_clearance_diameter + clamp.m16_diameter_compensation) / 2, 5)
        recess_center = clamp.cavity_bottom - clamp.sensor_head_recess / 2
        inner_plate -= _cylinder(
            x, y, recess_center, (clamp.sensor_head_diameter + clamp.head_diameter_compensation) / 2,
            clamp.sensor_head_recess,
        )

    # The central window preserves connector and cable access behind the sensor.
    inner_plate -= Pos(0, -21, -1.9) * Box(10.5, 12, 4)

    for y in clamp.bolt_stations_y:
        x_offset = clamp.cavity_half_width(y) + clamp.bolt_offset_from_cavity
        for x in (-x_offset, x_offset):
            bore = _cylinder(x, y, 5, (clamp.bolt_clearance_diameter + clamp.m3_diameter_compensation) / 2, 30)
            inner_plate -= bore
            outer_roof -= bore

            top = clamp.cavity_top(y) + clamp.roof_wall
            # V2 extends the cutter beyond the sloped exterior so no thin
            # partial skin remains across the high side of the pocket mouth.
            cut_height = 10 if clamp.open_head_pockets else clamp.bolt_head_recess
            outer_roof -= _cylinder(
                x, y, top - clamp.bolt_head_recess + cut_height / 2,
                (clamp.bolt_head_diameter + clamp.head_diameter_compensation) / 2,
                cut_height,
            )
            nut = extrude(
                RegularPolygon(radius=clamp.compensated_nut_radius, side_count=6),
                amount=clamp.nut_recess,
            )
            inner_plate -= Pos(x, y, clamp.plate_bottom) * nut

    # A transverse external tie hole anchors the moving cable without placing
    # a tie inside the finger cavity. Cable bend radius still needs a fit test.
    lug_bottom = clamp.cavity_top(clamp.tie_lug_y + clamp.tie_lug_length / 2) + clamp.roof_wall
    lug_center = lug_bottom + clamp.tie_lug_height / 2
    outer_roof += Pos(0, clamp.tie_lug_y, lug_center) * Box(
        clamp.tie_lug_width, clamp.tie_lug_length, clamp.tie_lug_height
    )
    if clamp.lug_print_ramp_run:
        start_y = clamp.tie_lug_y + clamp.tie_lug_length / 2
        end_y = start_y + clamp.lug_print_ramp_run
        end_z = clamp.cavity_top(end_y) + clamp.roof_wall
        # External triangular lead-in, grown while printing from distal to
        # proximal. A 0.1 mm root overlap makes the CAD union unambiguous.
        ramp = Face(Wire.make_polygon([
            (-clamp.tie_lug_width / 2, start_y, lug_bottom - 0.1),
            (-clamp.tie_lug_width / 2, start_y, lug_bottom + clamp.tie_lug_height),
            (-clamp.tie_lug_width / 2, end_y, end_z - 0.1),
        ]))
        outer_roof += extrude(ramp, amount=clamp.tie_lug_width, dir=(1, 0, 0))
    outer_roof -= (
        Pos(0, clamp.tie_lug_y, lug_center)
        * Rot(0, 90, 0)
        * Cylinder(clamp.tie_hole_diameter / 2, clamp.tie_lug_width + 2)
    )

    return inner_plate, outer_roof


def make_fit_gauge(clamp: ClampParameters):
    """Distal Y=-10..2.1: complete distal bolt pair, taper and end stop."""
    inner, roof = make_adapter(clamp)
    clip = Pos(0, -3.95, 0) * Box(150, 12.1, 100)
    return inner & clip, roof & clip


def make_fastener_coupon(clamp: ClampParameters):
    """Three labeled-by-map lanes; extra diametral/AF offsets 0/0.1/0.2 mm.

    Coupon axes: X is feature sequence, Y is lane, Z is print-up. The stepped
    M1.6 and M3 stations duplicate the modeled remaining bearing thickness.
    Do not apply a lane to the adapter until physical data is returned.
    """
    from dataclasses import replace

    coupon = Pos(0, 0, 1.3) * Box(48, 30, 2.6)
    for y, delta in ((-10, 0.0), (0, 0.1), (10, 0.2)):
        p = replace(clamp,
                    m16_diameter_compensation=clamp.m16_diameter_compensation + delta,
                    m3_diameter_compensation=clamp.m3_diameter_compensation + delta,
                    head_diameter_compensation=clamp.head_diameter_compensation + delta,
                    nut_across_flats_compensation=clamp.nut_across_flats_compensation + delta)
        # X=-18: M1.6 bore and head pocket in a 2.6 mm plate.
        coupon -= _cylinder(-18, y, 1.3, (p.sensor_clearance_diameter + p.m16_diameter_compensation) / 2, 5)
        coupon -= _cylinder(-18, y, 2.6 - p.sensor_head_recess / 2,
                            (p.sensor_head_diameter + p.head_diameter_compensation) / 2, p.sensor_head_recess)
        # X=-6: M3 bore; X=+6: M3 bore with shallow head pocket.
        for x in (-6, 6):
            coupon -= _cylinder(x, y, 1.3, (p.bolt_clearance_diameter + p.m3_diameter_compensation) / 2, 5)
        coupon -= _cylinder(6, y, 2.6 - p.bolt_head_recess / 2,
                            (p.bolt_head_diameter + p.head_diameter_compensation) / 2, p.bolt_head_recess)
        # X=+18: 2.6 mm deep hex pocket in a 3.6 mm local pad, M3 through bore.
        coupon += Pos(18, y, 3.0) * Box(9, 9, 1.2)
        nut = extrude(RegularPolygon(radius=p.compensated_nut_radius, side_count=6), amount=p.nut_recess + 0.1)
        coupon -= Pos(18, y, 1.0) * nut
        coupon -= _cylinder(18, y, 1.8, (p.bolt_clearance_diameter + p.m3_diameter_compensation) / 2, 5)
    # Orientation notch at (-X,-Y) identifies the 0.00 mm lane without text.
    coupon -= Pos(-24, -15, 1.3) * Box(3, 3, 5)
    return coupon
