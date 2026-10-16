"""V2 only. Millimetres, native gripper_link1 jaw frame; see docs/interface-spec.md."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parameters:
    # Recovered independently on both supplied jaw meshes, NOT physical metrology.
    mount_y: float = -70.0
    mount_hole_x: tuple = (-6.0, 6.0)
    mount_hole_z: tuple = (11.25, 19.25)
    carrier_z_min: float = 4.0
    carrier_z_max: float = 26.5
    # Authored dimensions and clearance allowances, all adjustable.
    flange_thickness: float = 6.0
    width: float = 28.0
    mount_bore: float = 2.4
    mount_screw_diameter: float = 2.0  # M2 inferred from 1.6 mm pilot; verify thread.
    mount_screw_length: float = 8.0  # Retains 2 mm nominal carrier penetration with 6 mm seat.
    mount_head_diameter: float = 3.8  # Candidate hardware envelope, not measured.
    mount_head_height: float = 2.0
    mount_head_pocket: float = 4.2
    mount_driver_diameter: float = 2.4  # Slim M2 hex driver; not a 1/4-inch bit holder.
    linkage_access_diameter: float = 4.0
    linkage_access_z: float = 12.25
    # Stock mating plane -> distal contact edge is 70 mm, measured on both meshes.
    tip_y: float = 3.2  # Holder edge; functional reach is the tactile crown at Y=0.
    sensor_frame_proximal_y: float = -24.5
    sensor_rear_z: float = 9.2
    rail_thickness: float = 5.5
    window_half_width: float = 7.0
    window_y_min: float = -22.0
    window_y_max: float = 1.7
    arm_front_z: float = 12.0
    arm_flange_thickness: float = 3.5
    arm_distal_top_z: float = 24.5
    rib_thickness: float = 5.0
    root_top_z: float = 31.0
    root_block_end_y: float = -56.0
    transition_fillet: float = 2.5
    service_window_y_min: float = -57.0  # Open service access; root collar and screw seats unchanged.
    service_window_y_max: float = -44.0
    service_window_half_width: float = 10.0
    service_window_radius: float = 3.0
    service_window_top_z: float = 24.0
    root_head_access_end_y: float = -48.0
    cable_slot_end_y: float = -54.0
    cable_slot_half_width: float = 4.5
    cable_slot_radial_clearance: float = 1.0
    tie_y: float = -42.0
    tie_slot_x: tuple = (-8.0, .8)
    tie_slot_width: float = 1.6
    tie_slot_length: float = 3.6
    saddle_y_min: float = -46.0
    saddle_y_max: float = -38.0
    saddle_thickness: float = 3.0
    saddle_cable_clearance: float = .3
    # Native STEP: exact axes differ by <0.001 mm from drawing's 3/11/19.
    sensor_hole_x: tuple = (-8.75, 8.75)
    sensor_hole_y: tuple = (3.0, 11.00025981292, 19.00051962584)
    sensor_native_rear_z: float = -2.15
    # Native proximal edge of the three broad tactile crown faces, independently
    # recovered from STEP. Align their distal edge to stock distal Y=0.
    sensor_y_translation: float = 1.602079903898
    sensor_bore: float = 2.1  # PETG clearance allowance; coupon calibration required.
    sensor_plate_thickness: float = 3.6  # One continuous flat screw-seating plate.
    sensor_access_half_width: float = 11.0
    sensor_access_y_min: float = -20.5
    sensor_access_y_max: float = 1.2
    sensor_access_radius: float = 2.0
    sensor_access_floor_radius: float = .4
    sensor_seat_chamfer: float = .15  # 45-degree bore-mouth relief for the ISO under-head blend.
    sensor_screw_lengths: tuple = (5.0, 5.0, 5.0)  # Same short screw at every position.
    sensor_thread_penetration: float = 1.4  # Into the manufacturer's 2 mm tapped depth.
    sensor_print_radial_error: float = .15  # Sensitivity case, NOT a measured printer capability.
    sensor_print_stack_error: float = .15  # +/- axial seat-to-sensor error, pending measurement.
    sensor_head_height: float = 1.6  # Illustrative head; check actual stock.
    sensor_rear_clearance: float = .6  # Shallow underside electronics relief; plate stays continuous.
    # Paired native +Y-facing DF53 receptacles; left port chosen for cable study.
    plug_center_x: float = -3.6
    socket_mouth_native_y: float = 18.52025982484
    plug_width: float = 6.5  # DF53-8P-0.6C catalog; verify actual harness housing.
    plug_exposed_length: float = 1.4  # Mated 3.55 minus receptacle 2.15.
    plug_height: float = 1.35
    plug_native_z_min: float = -1.10
    cable_native_z: float = -.65
    cable_width: float = 5.2  # Clearance envelope of eight loose leads, NOT measured cable.
    cable_thickness: float = 1.0
    straight_exit: float = 12.0
    cable_bend_radius: float = 38.0  # Broad remote bend, after straight run.
    fixed_loom_x: float = -55.0  # Base-frame provisional fixed harness restraint.
    fixed_turn_radius: float = 25.0
    loop_turn_u_closed: float = 85.0
    manufacturer_min_bend_radius: float | None = None

    @property
    def flange_front_y(self):
        return self.mount_y + self.flange_thickness

    @property
    def rail_back_z(self):
        return self.sensor_rear_z + self.rail_thickness

    @property
    def arm_rear_slope(self):
        return (self.arm_distal_top_z-self.root_top_z)/(self.sensor_frame_proximal_y-self.root_block_end_y)

    @property
    def sensor_z_translation(self):
        return self.sensor_rear_z + self.sensor_native_rear_z

    @property
    def sensor_axes(self):
        return [(x, self.sensor_y_translation - y)
                for x in self.sensor_hole_x for y in self.sensor_hole_y]

    def sensor_screw_length(self, y):
        row = min(range(3), key=lambda i: abs(self.sensor_y_translation-self.sensor_hole_y[i]-y))
        assert abs(self.sensor_y_translation-self.sensor_hole_y[row]-y) < 1e-6
        return self.sensor_screw_lengths[row]

    def sensor_screw_seat_z(self, y):
        return self.sensor_rear_z + self.sensor_plate_thickness

    @property
    def plug_mouth_y(self):
        return self.sensor_y_translation - self.socket_mouth_native_y

    @property
    def cable_start_y(self):
        return self.plug_mouth_y - self.plug_exposed_length

    @property
    def cable_z(self):
        return self.sensor_z_translation - self.cable_native_z

    @property
    def bend_start_y(self):
        return self.cable_start_y - self.straight_exit

    @property
    def loop_radius(self):
        return (self.plug_center_x - self.fixed_loom_x) / 2

    def check(self):
        assert self.width/2-self.sensor_access_half_width >= 3.0
        assert self.mount_y < self.flange_front_y < self.sensor_frame_proximal_y < self.window_y_min < self.window_y_max < self.tip_y
        assert self.window_half_width < min(abs(x) for x in self.sensor_hole_x) - self.sensor_bore / 2
        assert all(abs(length-self.sensor_thread_penetration-self.sensor_plate_thickness) < 1e-8
                   for length in self.sensor_screw_lengths)
        assert 2.5 <= self.sensor_plate_thickness <= 4.0
        assert self.sensor_plate_thickness-self.sensor_rear_clearance >= 3.0
        assert self.sensor_access_half_width-max(self.sensor_hole_x) >= 2.0
        assert self.tip_y-self.sensor_access_y_max >= 2.0
        assert 0 <= self.sensor_seat_chamfer <= .2
        assert self.sensor_rear_z > 8.203  # Full-travel separation; actual CAD also checked.
        assert self.rib_thickness > 0 and self.flange_thickness > 0
        assert self.root_top_z > self.carrier_z_max
        assert self.mount_y < self.flange_front_y < self.root_block_end_y < self.service_window_y_max < self.sensor_frame_proximal_y
        assert self.width/2-self.service_window_half_width >= 4
        assert min(self.cable_bend_radius, self.loop_radius, self.fixed_turn_radius) >= 25
        assert self.straight_exit >= 12 and self.cable_thickness < self.plug_height


P = Parameters()
