# Mechanical requirements and status

The adapter must mount two M2324 tactile sensors, one on each existing AgileX Piper gripper finger, with active faces opposed and without replacing, drilling, machining, or permanently altering stock parts. Each clamp should be removable, fastener-retained, parametric, printable by FDM, and keep its sensing face exposed and cable clear of motion. Adhesive alone is not an acceptable primary attachment.

| Item | Design reference | Status |
| --- | --- | --- |
| Gripper | Supplied Piper Xacro and AGX gripper meshes | Reference geometry inspected; physical finger unmeasured |
| Sensors | Two IP-M2324-Core units; user confirmed M2324 | Supplied CAD profile used twice; physical units unmeasured |
| Mounting interface | Supplied M2324 six M1.6 blind holes | CAD axes verified; actual hardware unmeasured |
| Coordinate frame | Jaw-local X across width, Y toward distal tip, Z away from grasp gap | Defined in `cad/source/parameters.py`; mesh/URDF metre to CAD millimetre conversion checked |
| Fasteners and fit | Four M3 clamp bolts, six M1.6 sensor screws, nominal 0.5–0.7 mm bare cavity clearance | Geometry checked; screw fit and liner compression untested |
| Material and process | Initial PETG FDM prototype | Printing and strength untested |
| Cable routing | Proximal plate window and external tie lug | Solid clearance checked; plug and bend radius unmeasured |
| Operating opening | Provisional floor 25 mm commanded gap | Paired-jaw envelope check passes with ≥2 mm gap at 25, 50, 100 mm; full closure conflicts |

Record physical values, method, uncertainty, and date in `measurements/gripper/` and `measurements/sensor/`. See [dimensional-checklist.md](dimensional-checklist.md) before making a final print.
