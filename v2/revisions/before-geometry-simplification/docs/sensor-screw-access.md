# M2324 short mounting pads and open screw access

**Every head seat is now Z=12.8, only 3.6 mm behind the unchanged sensor plane Z=9.2.** The old 6.6 / 10.6 / 14.6 mm passages and six cylindrical towers are removed. All six positions use the same candidate **M1.6×5** screw. No counterbore depth is being substituted for the actual pass-through thickness.

All six positions pass reference-hardware CAD insertion, seating, tightening and removal checks with the finger attached. Actual hardware, printed fit and usable full thread engagement remain **UNVERIFIED**. S1–S3 are X=−8.75 from distal to proximal; S4–S6 are X=+8.75 in the same order. There are six screws per finger, twelve for the two-finger assembly.

| Screw | M1.6 length (mm) | Actual seat-to-sensor stack (mm) | Insert / seat | Tighten / remove | Open side access | Actual hardware | Min free / driver clearance (mm) | Blade reach beside adjacent wall (mm) |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| S1 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 3.423 |
| S2 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 6.253 |
| S3 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 9.084 |
| S4 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 3.423 |
| S5 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 6.253 |
| S6 | 5 | 3.6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 / 0.75 | 9.084 |

## Local mounting geometry

Six short **6 × 6 mm rounded flanges** support the heads. All seats are flat at Z=12.8, giving **3.6 mm pass-through** over the sensor mounting strips. The small lips added toward the electronics window start at Z=9.8, so their minimum thickness is **3.0 mm** and they do not contact the electronics. Ø2.1 clearance bores retain a 0.15 × 45° mouth relief (Ø2.4 mouth). Minimum bore-to-pad-edge ligament is **1.95 mm**; nominal head-to-pad-edge distance is **1.50 mm**. The minimum ISO Ø2.72/Ø2.4 bearing annulus is fully supported, area **1.287 mm²**.

**4.5 mm wide U pockets** open from each seat into the existing central sensor window. They extend through the local sloping material above the pads and have **R0.4 floor transitions**. The outer rail stays continuous at **3 mm wide**, with **3.5 mm longitudinal ligaments between adjacent pocket openings**. The head sits directly on the flange; there is no enclosing counterbore or long cylindrical tool tunnel. The head-width lateral corridor is checked for zero material overlap from each seat up to open space. Adjacent reinforcing walls remain tall; their height is reported as blade reach, not as screw pass-through thickness.

The sensor-interface alteration preserves the **5 mm main webs, root collar and 6 mm root seat**. Exact boolean comparison of the preserved short-pad and long-passage solids finds zero change outside the six mounting zones. The current part also incorporates the separately checked printability correction: moving the inner core roof down **0.074 mm** makes the sloped rear skin **3.5 mm perpendicular to its surface**, instead of 3.428 mm. That correction adds **40.319 mm³** only at the core roof; no material is removed and no sensor/root interface moves. The original outer 3 mm rails still match the preserved reinforcement. Sensor-zone material removed is **1279.301 mm³**, added **7.899 mm³**. The actual part is **one valid connected solid**; no removable plate or extra joint is needed. Local pad strength and torque capacity remain physically unverified.

## Screw and driver basis

[NBK SNS/SNSS-M1.6-5](https://www.nbk1560.com/images/en/product/miniaturescrew/SNS/SNS_1.pdf) documents a standard **5 mm** screw with **0.35 pitch, Ø3 × 1.6 head and 1.5 mm hex drive**. The [ISO/JIS extract](https://www.nbk1560.com/images/en/product/technical_data/rokkaku_bolt_NBK/rokkaku_bolt_NBK_1.pdf) supplies length bounds **4.76–5.24 mm**, maximum knurled head Ø3.14, under-head blend R0.2, minimum bearing Ø2.72, socket AF1.52 and minimum depth 0.7. These are parameterized reference dimensions, not measurements of supplied screws. The CAD includes the head, socket and blend; threads use their major-diameter envelope.

The manufacturer's six **M1.6 tapped holes, 2 mm depth**, 17.5 mm horizontal and 8 mm vertical pitch remain authoritative. Every vendor STEP axis is remeasured; its Ø1.25 minor cylinder is not treated as a clearance hole. Sensor location and orientation are unchanged.

The reference [Wera 2054 Micro 05118066001](https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118066001.pdf) has a **1.5 mm hex, Ø3 mm shaft and 60 mm blade**, modeled with 0.7 mm axial engagement. Its [product table](https://www.wera.de/en-au/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications) gives 97 mm handle length; the handle diameter is an explicit assumed Ø20 mm envelope. Actual tip transition, handle and torque-bearing socket engagement remain unverified. Each tool pose is an alternative, one screw at a time.

## PETG allowance and thread depth

Nominal driver clearance to the pocket walls is **0.75 mm radial**. Minimum free screw-to-finger clearance is **0.1414 mm** at the under-head blend; deliberate flat-seat and thread contact are excluded. With a uniform **0.15 mm radial hole/pocket undersize** case, Ø1.8 bores and 4.2 mm pockets still pass every screw and tool sweep. Driver clearance is then **0.60 mm**, shank clearance 0.10, and minimum blend clearance **0.0354 mm**. These are stated error assumptions, not measured printer capability. Position error, ovality and support residue remain physical checks. The existing coupon now reproduces the **3.6 mm pass-through thickness** and bore-mouth relief.

All six screws penetrate **5 − 3.6 = 1.4 mm nominally**, leaving **0.6 mm** to the manufacturer's 2 mm depth. Screw-length tolerance gives **1.16–1.64 mm** penetration. Including an assumed **±0.15 mm printed-stack error** gives **1.01–1.79 mm**, leaving **0.21 mm minimum nominal-depth margin**. Tap lead, fully formed thread depth, screw-tip shape, actual sensor depth tolerance and permissible torque are unknown. Check actual protrusion before assembly; a 6 mm screw is not a substitute in this 3.6 mm stack.

## Complete assembly verification

Continuous 30 mm axial insertion/removal sweeps include the maximum screw length and Ø3.14 head rotation envelope. Only the matching Ø1.6 shaft volume within the documented 2 mm tap depth is exempted as intended thread contact. The audit includes both attached fingers, sensor housings, original moving blocks, other installed screws, plug, leads, tie, service loops and the conservative bounding envelope of the complete original actuator at commands 0/50/100. Same-jaw poses remain fixed, opposing-jaw separation increases with opening, and actuator axial separation is constant. The robot arm, surrounding workcell and hands are outside the supplied standalone model.

[Old/new cross-section at the same scale](../drawings/sensor_screw_seating.png) · [six open access paths](../drawings/sensor_screw_access.png) · [complete driver/assembly view](../drawings/sensor_screw_access_assembly.png) · [interactive CAD](../cad/exported/sensor_screw_access.glb) · [access STEP](../cad/exported/sensor_screw_access.step) · [machine results](sensor-screw-access.json). Units are mm; GLB uses metres. The existing [PRINT-HOLD](../../PRINT-HOLD.md) and [fit checklist](../measurements/fit-checklist.md) remain in force.
