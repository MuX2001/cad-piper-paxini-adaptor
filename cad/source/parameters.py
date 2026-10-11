"""Millimetre parameters for the preliminary Piper finger clamshell."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClampParameters:
    # Jaw-local axes follow the supplied gripper_link1 STL: distal end at Y=0,
    # stock contact side near Z=0, and X across the finger width.
    proximal_y: float = -26.0
    distal_y: float = 2.1
    cavity_proximal_y: float = -27.0
    cavity_distal_y: float = 0.6
    cavity_half_width_proximal: float = 16.2
    cavity_half_width_distal: float = 11.9
    cavity_top_proximal: float = 11.7
    cavity_top_distal: float = 8.1
    cavity_bottom: float = -0.6
    side_wall: float = 9.0
    roof_wall: float = 3.0
    plate_bottom: float = -3.2
    split_z: float = 4.0
    bolt_offset_from_cavity: float = 4.5
    bolt_stations_y: tuple[float, float] = (-20.0, -6.0)
    bolt_clearance_diameter: float = 3.4
    bolt_head_diameter: float = 6.2
    bolt_head_recess: float = 2.2
    nut_circumradius: float = 3.3
    nut_recess: float = 2.6
    sensor_clearance_diameter: float = 1.8
    sensor_head_diameter: float = 3.2
    sensor_head_recess: float = 1.2
    tie_lug_y: float = -23.0
    tie_lug_width: float = 12.0
    tie_lug_length: float = 6.0
    tie_lug_height: float = 6.0
    tie_hole_diameter: float = 3.2

    def cavity_half_width(self, y: float) -> float:
        fraction = (y - self.cavity_proximal_y) / (
            self.cavity_distal_y - self.cavity_proximal_y
        )
        return self.cavity_half_width_proximal + fraction * (
            self.cavity_half_width_distal - self.cavity_half_width_proximal
        )

    def cavity_top(self, y: float) -> float:
        fraction = (y - self.cavity_proximal_y) / (
            self.cavity_distal_y - self.cavity_proximal_y
        )
        return self.cavity_top_proximal + fraction * (
            self.cavity_top_distal - self.cavity_top_proximal
        )


@dataclass(frozen=True)
class M2324Reference:
    """Dimensions measured from the supplied M2324 CAD reference."""

    model: str = "IP-M2324-Core PXSR-STDIP03A"
    hole_x: tuple[float, float] = (-8.75, 8.75)
    hole_y_native: tuple[float, float, float] = (3.0, 11.0, 19.0)
    sensor_y_translation: float = -0.8
    sensor_z_translation: float = -5.35
    back_plane_native_z: float = -2.15
    tapped_depth: float = 2.0

    @property
    def hole_positions_in_jaw(self) -> tuple[tuple[float, float], ...]:
        # The STEP solid is rotated 180 degrees about X to face the grasp gap.
        return tuple(
            (x, self.sensor_y_translation - y)
            for y in self.hole_y_native
            for x in self.hole_x
        )
