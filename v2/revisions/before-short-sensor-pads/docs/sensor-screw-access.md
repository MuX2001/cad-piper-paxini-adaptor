# Six-screw M2324 assembly-access verification

All six positions **PASS the reference-hardware CAD checks** for insertion, seating, tightening and removal with the finger attached to the moving block. Actual hardware and PETG fit remain **UNVERIFIED**. No supplied screw or screwdriver specification exists beyond the sensor manufacturer's hole callout; catalog hardware is a parameterized design basis, not an approved physical BOM.

S1–S3 are jaw X=−8.75, distal to proximal; S4–S6 are X=+8.75 in the same order. Each finger uses two screws of each length; the complete pair uses four each.

| Screw | M1.6 length (mm) | Stack / minimum floor (mm) | Insert / seat | Tighten / remove | Geometric engagement | Actual hardware | Min free / driver clearance (mm) | Bottom margin incl. stated errors (mm) |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| S1 | 8 | 6.6 / 6.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.16 |
| S2 | 12 | 10.6 / 10.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.10 |
| S3 | 16 | 14.6 / 14.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.10 |
| S4 | 8 | 6.6 / 6.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.16 |
| S5 | 12 | 10.6 / 10.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.10 |
| S6 | 16 | 14.6 / 14.0 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.60 | 0.10 |

## Local geometry and retained structure

Each mounting pad is **Ø7.2**, with a **Ø4.2 × 2 mm deep counterbore**, **1.5 mm radial rim**, and **Ø2.1 through bore**. The 0.15 × 45° bore-mouth relief opens to Ø2.4 and clears the under-head blend. Minimum ISO bearing annulus Ø2.72/Ø2.4 is fully supported: 1.287 mm² per screw. Bearing contact intentionally has zero clearance; it is excluded from the free-surface minimum.

Local seat Z is **15.8 / 19.8 / 23.8 mm**; pad tops are **17.8 / 21.8 / 25.8 mm**. Seat-to-sensor stack is **6.6 / 10.6 / 14.6 mm**. Across the full counterbore footprint, the raised underside over the electronics window makes the minimum continuous floor **6.0 / 10.0 / 14.0 mm**. A wider shank passage and a shallow pocket replace the former deep head tunnels; no long narrow tool tunnel remains.

The **5 mm webs, 3.5 mm skins and 6 mm root seat** are unchanged. Exact boolean comparison against the [preserved prior reinforced V2](../revisions/before-shallow-counterbores/cad/exported/replacement_finger.step) finds **zero change outside the six Ø7.2 local zones**, and zero change in the root/arm region. Local material added is 1009.505 mm³ and removed is 19.722 mm³; net addition is 989.783 mm³. The sensor plane, 17.5 × 8 mm pattern, 70 mm functional reach, cable path and PiPER interfaces remain fixed. The earlier 47-file snapshot is also retained.

## Hardware basis

Catalog examples are Accu [M1.6×8](https://www.accu.co.uk/metric-cap-head-screws/3784-SSCF-M1-6-8-A2), [M1.6×12](https://www.accu.co.uk/metric-cap-head-screws/3786-SSCF-M1-6-12-A2) and [M1.6×16](https://www.accu.co.uk/metric-cap-head-screws/3038-SSC-M1-6-16-A4), all socket caps with **Ø3 × 1.6 mm heads, 1.5 mm hex drives and 0.35 mm pitch**. The [NBK ISO 4762/JIS table](https://www.nbk1560.com/images/en/product/technical_data/rokkaku_bolt_NBK/rokkaku_bolt_NBK_1.pdf) supplies conservative dimensional bounds: knurled-head maximum Ø3.14, under-head blend R0.2, minimum bearing Ø2.72, socket AF1.52 and depth0.7. Length bounds used are 7.71–8.29, 11.65–12.35 and 15.65–16.35 mm. Exact purchased lengths, finishes and head styles remain unconfirmed. The CAD models include heads, hex sockets and blends; threads use their Ø1.6 major-diameter envelope, without an invented mating helix.

The manufacturer specifies **six M1.6 tapped holes, 2 mm thread depth**, with 17.5 mm horizontal and 8 mm vertical pitch (supplied manual PDF p.8 and user confirmation). All six STEP holes contain Ø1.25 minor cylinders, 2 mm long; they are not clearance holes. Fully formed thread depth, tap lead and tightening torque cannot be established from smooth CAD pilots.

## Driver access and PETG allowances

The reference [Wera 2054 Micro 05118066001](https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118066001.pdf) has a 1.5 mm hex, **Ø3 mm shaft and 60 mm blade**. Nominal engaged length is **0.7 mm**. Only **1.1 mm** of slender reach is needed below each pad top, leaving **58.9 mm** before the modeled handle begins. The [product page](https://www.wera.de/en-au/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications) calls 97 mm the handle length; the ambiguous PDF label is resolved conservatively to that longer interpretation. Handle diameter remains an explicit **assumed Ø20 mm**; its full envelope is checked. Actual tip transition/chamfer and torque-bearing engagement remain unverified.

Nominal radial clearance is **0.60 mm for the driver/plain head**, **0.53 mm for a Ø3.14 knurled head**, and **0.25 mm for the screw shank**. The minimum free screw-surface clearance is **0.1414 mm**, at the relieved under-head blend. This replaces the former 0.10 mm driver gap.

A uniform **0.15 mm radial hole undersize** (0.30 mm on diameter) sensitivity is checked by rebuilding the finger with Ø1.8 bores and Ø3.9 counterbores. All six insertion and tool sweeps still clear: driver **0.45 mm**, maximum head **0.38 mm**, shank **0.10 mm** radial; blend minimum **0.0354 mm**. This error envelope is a design check, not a measured PETG capability. Hole position, ovality, support residue and real layer quality still need the existing fit check. The updated coupon reproduces the 2 mm pocket and relief in the existing 5.5 mm coupon body; it does not reproduce all three long shank stacks.

## Engagement and complete assembly checks

All lengths give **1.4 mm nominal penetration**, leaving **0.6 mm** to the manufacturer's nominal 2 mm depth. ISO screw-length tolerance alone leaves at least **0.31 / 0.25 / 0.25 mm**. Combining it with an explicit **±0.15 mm printed stack error** gives penetration **0.96–1.84 / 0.90–1.90 / 0.90–1.90 mm**, leaving **0.16 / 0.10 / 0.10 mm** respectively. Sensor depth tolerance, tap lead and screw-tip shape are unknown; therefore usable full-thread engagement, strength and actual non-bottoming remain physical checks. Measure protrusion before assembly; keep lengths assigned to their rows and do not substitute a longer screw.

Continuous 30 mm axial insertion/removal sweeps include the maximum screw length and Ø3.14 head rotation envelope. The only exempt housing overlap is the matching coaxial Ø1.6 volume within the documented threaded depth. Tightening uses the engaged hex plus shaft; the driver socket fit is checked separately. Checks include both attached fingers, the full sensor housing, actual retained blocks, other installed screws, opposite jaw, plug, leads, tie and service loops at q=0/50/100. The entire actuator mesh is bounded conservatively to prove separation. Same-jaw poses are fixed, the paths point outward, opposite-jaw separation increases with opening, and actuator axial separation is constant. The robot arm, workcell and hand ergonomics are outside the supplied standalone gripper model.

[Machine results](sensor-screw-access.json) · [six access paths](../drawings/sensor_screw_access.png) · [counterbore section](../drawings/sensor_screw_seating.png) · [complete assembly/tool view](../drawings/sensor_screw_access_assembly.png) · [interactive complete CAD](../cad/exported/sensor_screw_access.glb) · [local STEP study](../cad/exported/sensor_screw_access.step). All dimensions are mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
