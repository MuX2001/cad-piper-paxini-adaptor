# Preliminary print and assembly guide

**Profile:** The current exports use the supplied **IP-M2324-Core** STEP model. Install two of these sensors with their active faces facing each other. Complete the [dimensional checklist](dimensional-checklist.md) for **both** physical fingers and sensors before mounting live hardware.

## Parts and hardware

| Item | Quantity | Notes |
| --- | ---: | --- |
| Printed inner plate and outer roof | 2 each | Same STEP and STL designs on both fingers; millimetres |
| M2324 sensor | 2 | Supplied IP-M2324-Core interface; verify each physical unit |
| M3 hex nut | 8 | Nominal 5.5 mm across flats; check the printed traps |
| M3 pan/socket screw | 4 × 16 mm, 4 × 14 mm | Longer pair per jaw at proximal Y = −20 mm; shorter at distal Y = −6 mm. Confirm actual head diameter ≤6.2 mm and protrusion after assembly. |
| M1.6 screw | 12 × 3 mm | Six per sensor; 2 mm deep tapped holes, head diameter ≤3.2 mm. Verify length and thread engagement on real sensors. |
| Compliant liner | As fitted on both jaws | Start with roughly 0.7–0.8 mm removable elastomer strips on the printed cavity roof and plate. Keep them off the sensors and moving gripper surfaces. |
| Small cable tie | 2 | One per external tie hole; check each cable bend radius. |

## Printing

Print the two short `piper_finger_fit_gauge_*.stl` parts first and check **both** distal fingers without forcing the fit. For the full parts, use PETG as a practical initial material for a clamp; [Prusa's PETG guide](https://help.prusa3d.com/article/petg_2059) describes its use in mechanical holders and clamps. Start with a 0.4 mm nozzle, 0.2 mm layers, four perimeters, and 35% infill; these are trial settings, not strength validation. Print two inner plates with their flat sensor-mounting exteriors on the bed and two outer roofs with their flat split faces on the bed. Inspect the nut pockets and transverse tie holes in the slicer for bridging or local support needs. Do not scale the unitless STLs: their numbers are millimetres.

## Assembly and first movement

1. Deburr both printed sets. Trial-fit each pair of halves and four nuts around its **unmodified** stock finger. Confirm each end cap has clearance and neither finger is pinched by hard plastic.
2. Fit removable liner strips to both printed cavities as needed for a firm, reversible grip. The tapered fingers and distal caps resist axial sliding; four M3 screws per jaw supply preload. Tighten evenly by hand and stop if the plastic distorts or the gripper coating marks.
3. With both sensors disconnected and supported, fasten each mounting face to an inner plate with six M1.6 screws. Check that neither set of screw tips bottoms in the 2 mm blind holes. The active faces must point toward **each other** and remain uncovered.
4. Route each lead through its proximal window. Secure separate service loops to the external roof lugs without pulling on either connector. Keep both leads clear of both moving jaws over their permitted motion.
5. Install a clamp on each finger. Before powered motion, set a provisional **minimum commanded opening of 25 mm**. At 0 mm command, the paired sensor envelopes overlap by about 22.8 mm; do not command full closure with both installed.
6. Move slowly from 100 mm toward 25 mm while observing both clamps, sensors, and cables. Stop at unexpected contact. Begin grasp testing at low force only after both fit and clearance checks pass.

No physical fit, fastener torque, grip load, or cable bend test has been performed. See [validation-report.md](validation-report.md) for the checks that were run.
