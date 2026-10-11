"""Parametric two-piece, bolted clamp for the unmodified Piper jaw."""

from build123d import Box, Cylinder, Pos, RegularPolygon, Rot, Solid, Wire, extrude

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

    # Saw-free virtual split; the flat mating planes are also print-bed faces.
    lower_clip = Pos(0, 0, clamp.split_z - 50) * Box(150, 150, 100)
    upper_clip = Pos(0, 0, clamp.split_z + 50) * Box(150, 150, 100)
    inner_plate = shell & lower_clip
    outer_roof = shell & upper_clip

    for x, y in sensor.hole_positions_in_jaw:
        inner_plate -= _cylinder(x, y, -1.9, clamp.sensor_clearance_diameter / 2, 5)
        recess_center = clamp.cavity_bottom - clamp.sensor_head_recess / 2
        inner_plate -= _cylinder(
            x, y, recess_center, clamp.sensor_head_diameter / 2,
            clamp.sensor_head_recess,
        )

    # The central window preserves connector and cable access behind the sensor.
    inner_plate -= Pos(0, -21, -1.9) * Box(10.5, 12, 4)

    for y in clamp.bolt_stations_y:
        x_offset = clamp.cavity_half_width(y) + clamp.bolt_offset_from_cavity
        for x in (-x_offset, x_offset):
            bore = _cylinder(x, y, 5, clamp.bolt_clearance_diameter / 2, 30)
            inner_plate -= bore
            outer_roof -= bore

            top = clamp.cavity_top(y) + clamp.roof_wall
            outer_roof -= _cylinder(
                x, y, top - clamp.bolt_head_recess / 2,
                clamp.bolt_head_diameter / 2, clamp.bolt_head_recess,
            )
            nut = extrude(
                RegularPolygon(radius=clamp.nut_circumradius, side_count=6),
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
    outer_roof -= (
        Pos(0, clamp.tie_lug_y, lug_center)
        * Rot(0, 90, 0)
        * Cylinder(clamp.tie_hole_diameter / 2, clamp.tie_lug_width + 2)
    )

    return inner_plate, outer_roof
