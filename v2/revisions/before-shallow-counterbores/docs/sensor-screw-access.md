# Six-screw M2324 assembly-access verification

All six locations pass the **documented reference-hardware geometry check after a local seating correction**. Actual screw/tool selection and physical fit remain **UNVERIFIED**: the user confirmed that no additional hardware specification is available. This is not a print release. IDs S1–S3 are jaw X=−8.75 from distal to proximal; S4–S6 are X=+8.75 in the same order. Both complete jaw assemblies are checked.

| Screw | Jaw X, Y (mm) | Axial insertion | Driver / removal path | Geometric depth / usable thread | Overall actual hardware | Min free / head radial / driver radial clearance (mm) | Required slender reach (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | -8.75, -1.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 4.193 |
| S2 | -8.75, -9.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 7.023 |
| S3 | -8.75, -17.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 9.854 |
| S4 | 8.75, -1.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 4.193 |
| S5 | 8.75, -9.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 7.023 |
| S6 | 8.75, -17.398 | PASS | PASS | PASS / UNVERIFIED | UNVERIFIED | 0.0354 / 0.100 / 0.100 | 9.854 |

The minimum free clearance is **0.0354 mm at the maximum under-head blend**, excluding intentional flat-seat and thread contact. Plain head and shaft paths have 0.100 mm radial clearance. A generic ISO knurled head can reach Ø3.14 and would leave only 0.030 mm radial clearance in the existing Ø3.2 pocket; it is not interchangeable with the checked plain Ø3.0 head without confirming fit. No PETG tolerance is inferred from these nominal CAD values.

## Hardware basis and seating correction

The supplied PaXini manual (PDF p.8, printed p.5) calls out six **M1.6 tapped holes, depth 2 mm**. All six source STEP holes have Ø1.25 minor cylinders, native Z=−2.05…−0.05, consistent with tap pilots rather than clearance holes. The STEP has no thread helix. A physical thread gauge, usable full-flank depth and permissible tightening torque are unavailable.

The reference is a **plain-head M1.6×4, pitch 0.35 mm** socket screw; [NBK SNS/SNSS-M1.6-4](https://www.nbk1560.com/images/en/product/miniaturescrew/SNS/SNS_1.pdf) documents the main dimensions. The [NBK ISO 4762/JIS dimensional table](https://www.nbk1560.com/images/en/product/technical_data/rokkaku_bolt_NBK/rokkaku_bolt_NBK_1.pdf) supplies the conservative bounds: head Ø3.0 × 1.6, minimum hex socket AF1.52/depth0.7, maximum under-head diameter2.0 and radius0.2, minimum bearing diameter2.72, and length3.76…4.24. The authored CAD includes the head, actual hex recess and maximum under-head blend. The threaded portion is a conservative Ø1.6 major-diameter envelope; detailed helical mating is unverified. No supplier screw file is claimed.

Before correction each maximum-radius blend overlapped the sharp printed seat edge by **0.005042 mm³**. Six **0.15 × 45° bore-mouth chamfers**, also reproduced in the fit coupon, remove that overlap. The seat stays at Z=11.8, the head pocket stays Ø3.2, and the finger's webs, skins, sensor datum and reach are unchanged. Total material removed is **0.4030 mm³**. The guaranteed Ø2.72/Ø2.10 flat bearing annulus remains fully supported; its area is 2.347 mm² per screw. Nominal zero gap at the flat seat is intended.

## Insertion, tightening and removal

Screws approach along jaw −Z from 30 mm outside the seated position, after the replacement finger is bolted to the moving block and the sensor is seated. Continuous swept volumes enclose both screw rotation and translation, including the maximum 4.24 mm length. The only exempt sensor contact is the matching coaxial Ø1.6 volume inside the documented 2 mm tapped depth. No housing/head interference is hidden by a blanket exemption.

The reference driver is [Wera 2054 Micro 05118066001](https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118066001.pdf): 1.5 mm hex, Ø3 mm shaft and 60 mm blade. A 0.7 mm engaged hex tip fits the minimum socket. The full shaft begins immediately above the head as a conservative bound. Its required slender reach varies with the sloped pocket lip as tabulated; the remaining blade extends beyond the lip before the handle begins. The [manufacturer's product page](https://www.wera.de/en-au/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications) labels 97 mm as handle length, while the PDF table ambiguously labels it overall length. The longer interpretation is used. Handle diameter is not dimensioned here, so an explicitly **assumed Ø20 × 97 mm handle envelope** is checked. The actual reduced-tip transition, tip chamfer, handle and torque-bearing engagement remain UNVERIFIED. These tool positions are alternatives, one screw at a time.

The checks include the reinforced finger, original sensor housing, both real moving blocks, other installed screws, opposite finger/sensor, plug, moving leads, service loops and tie at 0/50/100 mm commands. The unchanged actuator is loaded from its complete source mesh; separation from its enclosing box proves conservative clearance without approximating its interior. Same-jaw poses are fixed, the approach is outward, opposite-jaw separation increases with opening, and the actuator Z separation is constant. Removal uses the reverse axial path after unscrewing; root screws stay installed. The supplied standalone CAD does not include the robot arm or nearby workcell.

## Engagement and remaining physical checks

The 2.6 mm seat-to-sensor stack gives **1.4 mm nominal penetration** and **0.6 mm nominal margin** to the manual's 2 mm depth. Screw-length tolerance alone gives **1.16…1.64 mm penetration**, leaving at least **0.36 mm**; printed thickness and sensor depth tolerance are not included. The available fully formed thread engagement cannot be inferred from the smooth pilot, tap lead or screw-tip envelope. Thread holding strength and safe tightening torque are therefore UNVERIFIED for every screw. The manufacturer's generic screw torque is not a permissible torque for the sensor or PETG seat.

See [machine measurements](sensor-screw-access.json), [six paths](../drawings/sensor_screw_access.png), [seat section](../drawings/sensor_screw_seating.png), [complete assembly/tool view](../drawings/sensor_screw_access_assembly.png), [interactive complete CAD](../cad/exported/sensor_screw_access.glb), and [local B-rep access study](../cad/exported/sensor_screw_access.step). All measurements are in mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
