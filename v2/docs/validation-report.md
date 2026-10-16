# Simplified reinforced V2 — validation result

**CAD VALIDATED for the supplied/reference geometry. Slicing NOT VERIFIED; physical validation pending; not print-ready.** The [full acceptance table](printability-acceptance.md) separates these levels and records the user PETG/P2S baseline. The existing [PRINT-HOLD](../../PRINT-HOLD.md) remains unchanged.

The current V2 has one **22 × 21.7 mm R2 common access pocket**, a continuous **3.6 mm screw-bearing plate** and six Ø2.1 holes. The underside electronics clearance is 0.6 mm deep, leaving 3.0 mm central material. No sensor screw bosses, individual U pockets, head counterbores or enclosed arm core remain. A single circular cable-saddle section replaces the segmented loft. The root service opening, root screw/head passages, central linkage access, shallow electronics clearance, rear cable channel and tie slots remain functional.

The final finger is **28 × 73.2 × 27 mm**; functional tactile reach remains **70 mm**. CAD faces reduce **226 → 120**, finger STL triangles **25,536 → 12,508**, and solid CAD volume increases **22,245.073 → 25,772.860 mm³**. These volumes are geometry, not slicer material estimates. The part is one valid connected solid.

Exact comparisons preserve the root region Y≤−56 and continuous outer sensor rails. The PiPER and sensor patterns, sensor plane/orientation, mating geometry, connector pose and cable centerline are unchanged. Root seats measure 6.000 mm, preserved outer web bands 5.000 mm, and sampled solid middle-arm depth at least 13.711 mm normal to the outer slope. Root/arm sections retain or increase area and bending moments. The sensor section deliberately replaces tall dividers with the continuous low plate; local clamping strength is untested. Interface-specific thickness exceptions are documented in the acceptance table.

| Screw | Insert / seat | Tighten / remove | Minimum free screw clearance | Driver radial clearance | Actual hardware |
| --- | --- | --- | ---: | ---: | --- |
| S1 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |
| S2 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |
| S3 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |
| S4 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |
| S5 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |
| S6 | PASS | PASS | 0.1414 mm | 0.750 mm | UNVERIFIED |

All use reference **M1.6×5**, head Ø3 × 1.6, hex 1.5, at seat Z=12.8 above the sensor Z=9.2 plane. Nominal penetration is 1.4 mm with 0.6 mm remaining to the specified 2 mm depth. Length limits and assumed ±0.15 mm stack error leave 0.21 mm minimum margin. Driver clearance remains 0.60 mm under the stated radial undersize case. Actual screws, driver tip/handle, usable fully formed threads, print accuracy and torque remain unverified. The minimum free clearance excludes intended bearing/thread contacts. [Per-screw evidence](sensor-screw-access.md).

Continuous axial access sweeps include the finger, both retained PiPER blocks, complete actuator bounding envelope, sensor housings, opposite jaw, installed screws and cable envelopes. Five complete motion configurations and continuous separation arguments preserve the full 0–100 mm opening range. The conservative minimum sensor-envelope gap is 1.994608 mm at zero command. No robot motion was performed. The reference cable route clears the new part; the existing uncertainty about actual plug-latch withdrawal through the sensor housing remains recorded.

All six active STL files pass explicit edge/vertex manifold, connected-body, winding, degenerate/duplicate-face and self-intersection checks, with zero improper triangle intersections. Native and print placements are checked separately; STEP/source equality is verified by valid cuts in both directions. The common pocket is open and the enclosed arm core is gone. Its 17.7 mm straight closure span still requires accessible support or slicer bridge validation in the side-down orientation; actual supports and post-slice opening retention are NOT VERIFIED.

Exactly five final previews are in [drawings](../drawings): [part](../drawings/replacement_finger.png), [mount and section](../drawings/sensor_mount.png), [closed/open assembly](../drawings/assembly.png), [cable routing](../drawings/cable_routing.png), [print orientation](../drawings/print_orientation.png). All previous previews are preserved with the complete 74-file pre-simplification V2 snapshot. V1's 232 protected files and two user inputs, plus every prior archive, are unchanged; both legacy validators pass read-only.

[Print STL](../cad/exported/replacement_finger_print.stl) · [STEP](../cad/exported/replacement_finger.step) · [Machine assembly evidence](validation.json) · [Mesh and manufacturing evidence](printability-acceptance.json) · [Section comparison](mechanical-comparison.md) · [Build manifest](build-manifest.json).
