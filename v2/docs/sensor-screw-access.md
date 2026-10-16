# M2324 common screw-access pocket

One **22 × 21.7 mm rounded rectangular pocket, R2 corners**, replaces six individual U pockets and separate pads. A continuous planar seat at Z=12.8 is **3.6 mm** behind the unchanged sensor mounting plane Z=9.2. The six Ø2.1 bores have only a 0.15 × 45° mouth relief; **no head counterbores or screw towers** remain. The plate is 3.0 mm thick over the shallow 0.6 mm electronics clearance and 3.6 mm at the screw-bearing strips. Outer rails are 3.0 mm wide. The R0.4 pocket-floor transition is preserved.

Each head has a fully supported minimum ISO bearing annulus (Ø2.72 outside / Ø2.4 relief). The continuous plate replaces isolated lips and has at least 3.548 mm from bore to the external plate edge. Sensor location, 17.5 mm column pitch and 8 mm row pitch are unchanged; each of the six 2 mm blind M1.6 holes is remeasured in the vendor STEP.

S1–S3 are X=−8.75, distal to proximal; S4–S6 are X=+8.75. Six screws per finger, twelve total.

| Screw | Insert / seat | Tighten / remove | Attached-block assembly | Actual hardware | Min free screw clearance (mm) | Driver clearance (mm) | Required blade reach (mm) |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| S1 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 3.42 |
| S2 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 6.25 |
| S3 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 9.08 |
| S4 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 3.42 |
| S5 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 6.25 |
| S6 | PASS | PASS | PASS | UNVERIFIED | 0.1414 | 0.75 | 9.08 |

## Reference fasteners and tool

All six use candidate **M1.6×5**, nominal head **Ø3 × 1.6**, hex **1.5**, pitch **0.35**, per [NBK SNS/SNSS](https://www.nbk1560.com/images/en/product/miniaturescrew/SNS/SNS_1.pdf). The [ISO/JIS extract](https://www.nbk1560.com/images/en/product/technical_data/rokkaku_bolt_NBK/rokkaku_bolt_NBK_1.pdf) supplies 4.76–5.24 mm length limits, Ø3.14 maximum knurled head, R0.2 under-head blend, Ø2.72 minimum bearing and 0.7 mm minimum socket depth. The CAD includes head, socket and under-head blend; threads use a major-diameter envelope. No physical screw was supplied, so these are parameterized reference dimensions, not a verified BOM.

Reference [Wera 2054 Micro 05118066001](https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118066001.pdf): 1.5 mm hex, Ø3 mm shaft, 60 mm blade, modeled 0.7 mm axial engagement. A conservative Ø20 × 97 mm handle is parameterized; its diameter and exact tip transition are unverified. [Product table](https://www.wera.de/en-au/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications).

Nominal screw penetration is **1.4 mm**, with **0.6 mm** remaining to the manufacturer's 2 mm depth. Screw-length limits plus assumed ±0.15 mm printed-stack error give **1.01–1.79 mm** penetration and **0.21 mm** minimum depth margin. Fully formed thread engagement, tap lead, actual hole depth tolerance and safe torque remain UNVERIFIED. A 6 mm screw would bottom in this stack and is unsuitable.

## Clearance verification

Every seated screw, continuous 30 mm insertion/removal envelope, and driver shaft/handle sweep clears the finger and sensor, both attached moving blocks, the opposite jaw, installed hardware and harness, and the conservative complete-actuator bounding box at 0/50/100 mm. Reverse paths are identical after unscrewing. Same-jaw relative geometry is fixed through travel; separation from the opposing jaw increases with opening. Intended flat-seat and mating-thread contacts are excluded from free-clearance measurements.

Nominal shaft-to-pocket clearance is **0.75 mm radial**. A stated **0.15 mm radial undersize sensitivity** still clears all paths: driver 0.60 mm, screw shank 0.10 mm and under-head blend 0.0354 mm. This is not measured PETG printer accuracy. The existing coupon reproduces the 3.6 mm stack and bore-mouth relief. Position error, ovality, support residue and actual hardware fit require physical inspection.

[Mount close-up and section](../drawings/sensor_mount.png) · [Interactive complete assembly/access CAD](../cad/exported/sensor_screw_access.glb) · [Access STEP](../cad/exported/sensor_screw_access.step) · [Machine results](sensor-screw-access.json). PRINT-HOLD remains; no physical assembly or slicing has been validated.
