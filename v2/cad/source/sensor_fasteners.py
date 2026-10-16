"""Catalog-based sensor screw and driver clearance models, millimetres.

No physical screw/tool was supplied. See docs/sensor-screw-access.md. The
thread is its conservative major-diameter envelope, not a mating helix.
"""

from dataclasses import dataclass, replace
from math import cos, sin, pi, sqrt

from build123d import Face, GeomType, Plane, Pos, Solid, Wire

from v2_parameters import P


@dataclass(frozen=True)
class SensorFastener:
    screw_reference: str = "M1.6x5 ISO 4762 envelope; NBK SNS/SNSS-M1.6-5 reference; stock unconfirmed"
    screw_source: str = "https://www.nbk1560.com/images/en/product/miniaturescrew/SNS/SNS_1.pdf"
    dimensions_source: str = "https://www.nbk1560.com/images/en/product/technical_data/rokkaku_bolt_NBK/rokkaku_bolt_NBK_1.pdf"
    diameter: float = 1.6
    pitch: float = .35
    length: float = 5.0
    length_min: float = 4.76
    length_max: float = 5.24
    head_diameter: float = 3.0  # Maximum unknurled head; knurled bound is separate.
    knurled_head_max: float = 3.14
    head_height: float = 1.6
    underhead_radius: float = .2  # (da_max 2.0 - ds_max 1.6)/2.
    bearing_diameter_min: float = 2.72
    socket_af_min: float = 1.52
    socket_depth_min: float = .7
    tapped_depth_manual: float = 2.0
    driver_reference: str = "Wera 2054 Micro 05118066001, 1.5x60"
    driver_source: str = "https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118066001.pdf"
    driver_product_source: str = "https://www.wera.de/en-au/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications"
    driver_hex_af: float = 1.5
    driver_shaft_diameter: float = 3.0
    driver_blade_length: float = 60.0
    driver_handle_length: float = 97.0  # Wera product page labels this handle length.
    driver_handle_diameter_assumed: float = 20.0  # Not dimensioned by the manufacturer.
    driver_axial_engagement: float = .7
    insertion_travel: float = 30.0
    actual_hardware_confirmed: bool = False


S = SensorFastener()


def for_position(y,p=P,s=S):
    length = p.sensor_screw_length(y)
    tolerance = {4.0:.24,5.0:.24,6.0:.24}[length]  # ISO/JIS length bounds, NBK table.
    return replace(s,length=length,length_min=length-tolerance,length_max=length+tolerance)


def cylinder(x,y,z,diameter,length):
    return Solid.make_cylinder(diameter/2,length,Plane(origin=(x,y,z)))


def hex_prism(x,y,z,af,length):
    radius = af/sqrt(3)
    wire = Wire.make_polygon([(x+radius*cos(i*pi/3),y+radius*sin(i*pi/3),z)
                              for i in range(6)],close=True)
    return Solid.extrude(Face(wire),(0,0,length))


def sensor_screw(x,y,p=P,s=S):
    """Head, minimum socket and maximum under-head blend; major thread envelope.

    Flat head top/end are conservative: no arbitrary chamfers or thread shape
    are invented where the candidate's detailed CAD was not supplied.
    """
    s = for_position(y,p,s)
    assert abs(p.sensor_head_height-s.head_height) < 1e-9
    z = p.sensor_screw_seat_z(y)
    screw = cylinder(x,y,z-s.length,s.diameter,s.length)+cylinder(x,y,z,s.head_diameter,s.head_height)
    neck = [e for e in screw.edges() if e.geom_type==GeomType.CIRCLE
            and abs(e.radius-s.diameter/2)<1e-6 and abs(e.center().Z-z)<1e-6]
    assert len(neck)==1
    screw = screw.fillet(s.underhead_radius,neck)
    screw -= hex_prism(x,y,z+s.head_height-s.socket_depth_min,s.socket_af_min,s.socket_depth_min+.1)
    assert screw.is_valid and len(screw.solids())==1
    screw.label = f"M1.6x{s.length:g} catalog reference; physical hardware unconfirmed"
    return screw


def screw_insertion_sweep(x,y,p=P,s=S):
    """Continuous axial/rotational outer sweep, including the blend and max length.

    The head fills the socket in this conservative sweep. The shaft is its
    major diameter; only the matching tapped-hole volume is intentional contact.
    """
    s = for_position(y,p,s)
    z = p.sensor_screw_seat_z(y)
    shape = cylinder(x,y,z-s.length_max,s.diameter,s.length_max+s.insertion_travel)
    shape += cylinder(x,y,z,max(s.head_diameter,s.knurled_head_max),s.head_height+s.insertion_travel)
    shape += sensor_screw(x,y,p,s)
    return shape


def driver_components(x,y,p=P,s=S):
    top = p.sensor_screw_seat_z(y)+s.head_height
    tip = top-s.driver_axial_engagement
    # The full 3 mm shaft begins immediately above the head, conservatively
    # bounding the undocumented reduced-tip transition outside the socket.
    return {"engaged_hex_tip":hex_prism(x,y,tip,s.driver_hex_af,s.driver_axial_engagement),
            "shaft":cylinder(x,y,top,s.driver_shaft_diameter,s.driver_blade_length-s.driver_axial_engagement),
            "assumed_handle":cylinder(x,y,tip+s.driver_blade_length,s.driver_handle_diameter_assumed,
                                      s.driver_handle_length)}


def driver_sweeps(x,y,p=P,s=S):
    top = p.sensor_screw_seat_z(y)+s.head_height
    tip = top-s.driver_axial_engagement
    return {"tip_sweep":cylinder(x,y,tip,2*s.driver_hex_af/sqrt(3),
                                 s.driver_axial_engagement+s.insertion_travel),
            "shaft_sweep":cylinder(x,y,top,s.driver_shaft_diameter,
                                   s.driver_blade_length-s.driver_axial_engagement+s.insertion_travel),
            "handle_sweep_assumed":cylinder(x,y,tip+s.driver_blade_length,s.driver_handle_diameter_assumed,
                                           s.driver_handle_length+s.insertion_travel)}
