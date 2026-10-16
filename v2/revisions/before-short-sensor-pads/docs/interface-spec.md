# V2 coordinates and interface evidence

All dimensions are millimetres. “CAD verified” below means recovered from the supplied reference, not measured hardware. The source-derived measurements and file hashes are in `reference-measurements.json`; design values are in `../cad/source/v2_parameters.py`.

## Coordinates and conversion

The native jaw frame is retained: X across the finger, Y toward the original tip at Y = 0, Z outward from the grasping region. Original carrier mating face: Y = −70. The retained block occupies X = ±8.5, Y = −76.5…−70, Z = 4…26.5. The reinforced finger occupies X = ±14, Y = −70…3.2, Z = 4…31. Flat sensor seating strips remain at Z = 9.2; added depth is outward from the grasping gap.

In the gripper-base frame, Z runs away from the actuator and Y is the opening axis. For total command `q` in mm:

```text
jaw 1: (X, Y, Z) -> ( X, -Z - q/2, 138 + Y)
jaw 2: (X, Y, Z) -> (-X,  Z + q/2, 138 + Y)
```

These are the standalone supplied URDF transforms, with rounded π values replaced by exact rotations. The mimic multipliers are +0.5 and −0.5. Both printed fingers use the same geometry; no reflection/scaling is applied to manufacture the second part. Sensing normals are base +Y on jaw 1 and −Y on jaw 2.

Native M2324 coordinates map to jaw coordinates as `(x, 1.602079903898−y, 7.05−z)`: 180° about X, followed by translation (0, 1.602079903898, 7.05). Native rear Z = −2.15 therefore maps to 9.2; native +Z tactile surface faces inward. Sensor bounds are X = −11.894431…11.924621, Y = −21.206139…2.395368, Z = 0.997304…9.2 in each jaw frame. The sensing envelope is taken from the actual shape, not replaced by a bounding box in assembly views.

Vendor STL metre coordinates are multiplied by 1000 in memory. No original asset is rewritten or repaired. GLB is scaled back to metres. Manufacturing STEP/STL retain mm coordinates. The main print transform is `(x, y, z) -> (−z, y+70, x+14)`; the gauge is `(x, y, z) -> (x, 26.5−z, y+70)`. Both are proper rotations/translations with their bed at Z = 0.

## Original PiPER attachment

Each finger mesh contains a closed, separate **504-triangle moving block**. Its entire body is retained in the V2 assembly. The remaining 1,582 triangles of the original finger/pad geometry are omitted; this is body selection in a working assembly, not a cut through the stock part. Original references remain byte-for-byte intact.

Fitting circles to boundary loops on the actual front face at Y = −70 independently on both blocks gives:

| Feature | CAD result | Design use / status |
| --- | --- | --- |
| Four axes along Y | X = ±6; Z = 11.25 / 19.25 | Four Ø2.4 printed clearance holes; pitch 12 × 8 |
| Entrance radius | 1.025 | Chamfer, not a 2.05 mm thread specification |
| Blind pilot radius | 0.8 | Ø1.6 consistent with inferred M2; thread/pitch not represented |
| Cylindrical pilot interval | Y ≈ −72.5…−70.225 | Nominal 2 mm screw penetration avoids the modeled blind shoulder by 0.5 mm; real usable engagement unknown |
| Central through feature | X = 0, Z = 12.25; Ø3 | Ø4 clearance/access hole in printed flange; existing linkage unmodified |
| Stock removable finger holes | Ø2.4 at the same four axes | Supports clearance-hole interpretation; not a thread callout |

Circle-fit residuals are below 0.000001 mm, reflecting STL numeric precision, **not manufacturing accuracy**. A separate coincident interface and four matching holes make removal mechanically plausible in the CAD. The local assets do not prove how the real finger is retained or whether a specific hardware revision can be disassembled without disturbing the carriage. Verify before physical disassembly.

Four Ø4.2 head-access passages start at Y = −64, leaving the full **6 mm root bearing thickness**. M2×8 replaces the previous M2×6 candidate, retaining 2 mm nominal engagement. The reinforced root extends forward to Y ≈ −56 and has a rounded underside transition into the arm. A 20 × 13 mm nominal R3 service opening gives access to all four heads. It overlaps the core entrance by 1 mm to avoid coincident fillet seams. A Ø2.4 short L-key envelope can enter and turn 60° inward, sampled every 5°. Install root screws before sensors and harness. Long straight driver tunnels through the sensor rails are removed. The Ø4 central access passage reaches the service window; it remains access to the original feature, not another fastener or locating pin.

## M2324 installation

The supplied STEP has six cylindrical mounting axes at X = ±8.75 and native Y = 3, 11.00025981292, 19.00051962584. The drawing rounds the row pitch to 8 mm and column pitch to 17.5 mm. The rear face is native Z = −2.15; the provided manual identifies six M1.6 holes to 2 mm depth (PDF p. 8). The exact cylinder axes are recovered again during validation.

The six printed clearance holes are **Ø2.1 mm**, with **Ø4.2 × 2.0 mm shallow counterbores** in **Ø7.2 mm local pads**. The 1.5 mm radial rims retain material around each head. Local pads rise above the sloping reinforcement, so the original load-bearing members are not thinned to shorten screw passages. Added pad material begins at Z=9.8, 0.6 mm behind the sensor mounting plane; central electronics remain clear.

| Row / screw IDs | Candidate M1.6 length | Seat Z / pad top Z | Seat-to-sensor stack | Minimum floor under full counterbore |
| --- | ---: | ---: | ---: | ---: |
| Distal / S1, S4 | 8 mm | 15.8 / 17.8 mm | 6.6 mm | 6.0 mm |
| Middle / S2, S5 | 12 mm | 19.8 / 21.8 mm | 10.6 mm | 10.0 mm |
| Proximal / S3, S6 | 16 mm | 23.8 / 25.8 mm | 14.6 mm | 14.0 mm |

All six seats retain a 0.15 × 45° mouth relief, opening the Ø2.1 bore to Ø2.4. The minimum ISO Ø2.72/Ø2.4 flat bearing annulus is fully supported. Reference heads are Ø3 × 1.6, pitch0.35, 1.5 mm hex; conservative insertion sweeps also enclose Ø3.14 knurled heads. Hardware dimensions are parameterized in `sensor_fasteners.py`, row lengths and seat geometry in `v2_parameters.py`. The supplied stock and permissible torque remain unknown.

The [per-screw audit](sensor-screw-access.md) checks continuous insertion/removal and a catalog Ø3 mm / 60 mm / 1.5 mm hex driver on both complete attached-jaw models. Every location passes the reference geometry check. Slender reach below the local top is **1.1 mm** at all six; nominal driver radial clearance is **0.60 mm**. Minimum screw-to-finger free clearance is **0.1414 mm** at the under-head blend, excluding intended seat contact. A sensitivity case with holes 0.30 mm undersize on diameter still leaves 0.45 mm driver radial clearance and passes the sweeps; it is not a measured PETG tolerance.

Nominal penetration is **1.4 mm** for every row, leaving **0.6 mm** to the manufacturer's 2 mm depth. Screw-length tolerance plus an assumed ±0.15 mm stack error leaves minimum depth margins **0.16 / 0.10 / 0.10 mm**. Real thread depth tolerances, tap lead, usable full-flank engagement and torque strength are unverified. Measure actual protrusion, and keep the lengths assigned to their rows. The conservative sensor envelope still translates 12 mm toward the gap without catching the holder; sensor service leaves the root attached. **Actual hardware and physical fit are UNVERIFIED for S1–S6.**

## Functional reach and reinforcement

Both original meshes independently give mounting Y = −70.000000298 and distal Y ≈ 0: **70.000 mm reach**. The stock distal flat contact region is Y = −10.022178…0, with area 229.624 mm² and area centroid Y = −5.210419. These are geometric measurements, not physical metrology.

The sensor's three broad near-+Z crown faces have native Y = 1.602079903898…20.44664874099 and total area 318.942 mm². Selecting those faces excludes housing and peripheral bevels. After the stated transform, the tactile region spans jaw Y = **−18.844569…0**, or **51.155431…70.000 mm from the mount**. Its distal edge aligns with the stock tip and its longitudinal span covers the full stock distal pad. The sensor housing extends 2.395 mm and the holder 3.2 mm beyond the datum; neither is counted as tactile reach. The early goal-01 V2 translation of −39 gave only 29.397920 mm broad-crown reach; goal-02 corrected this to 70 mm, which goal-03 preserves. No vendor geometry is scaled.

The reinforced load path uses **5 mm main webs**, **3.5 mm skins** and a closed mid-span cell. The service opening locally leaves 4 mm side material. The outer profile reaches Z = 31 at the root, tapers to 24.5 at the sensor-frame entrance, and ends at the 14.7 mm rail back. Outer transitions use R2.5 fillets; the core has R2 fillets; the root service opening has R3 corners. The 3 mm curved cable saddle is retained at Y = −46…−38. Width stays 28 mm. A rounded rear channel follows the unchanged R38 cable path with 1 mm added radial clearance, preserving the root screw seats. Small tie slots cut the saddle without perforating the rear skin.

The [actual-section comparison](mechanical-comparison.md) evaluates the previous and current solids under matched representative loads. It shows increased gripping and lateral section stiffness, with a closed-cell shear path improving torsional geometry. Ideal beam estimates exclude bolted-joint compliance, shear, local notch stresses, printed anisotropy/defects and sensor case flexibility. Strength, fatigue and creep remain unverified; no operating-force or torque release follows.

## Motion and cable routing

For all q = 0…100 mm, each modeled rigid part stays on its own side of the central plane. The conservative sensor-envelope gap is `q + 1.994608484 mm`. The new finger starts at base Z = 68 mm, over 3 mm above the actuator's maximum Z ≈ 64.997852. Candidate root screw tips reach base Z = 66, retaining just over 1 mm of envelope separation. These constant Z margins prove separation from the supplied base mesh throughout pure jaw translation. They do not certify the internal mechanism, strength or real zero calibration.

The original STEP's paired proximal receptacle mouths lie at native X = ±3.6, Y = 18.52025982484, with exit normal **+Y**, parallel to the sensor plane. The chosen left port at X = −3.6 therefore exits along **jaw −Y**. The selected IN/OUT assignment is provisional. The catalog DF53-8P-0.6C plug is 6.5 mm wide and 1.35 mm high; the exposed mated projection is **1.40 mm**, from 3.55 mm total mated depth minus 2.15 mm receptacle depth. The whole unmated plug length is 2.82 mm. This authored plug envelope represents the exposed portion; it is not a supplied cable assembly model.

The plug mouth maps to Y = −16.918180; leads start at Y = −18.318180. The assumed loose-lead envelope is **5.2 × 1.0 mm**, allowing space around eight nominal 0.6 mm-pitch leads (catalog wire insulation max Ø0.4 mm). Actual harness bundling/sleeving dimensions remain unknown. The leads run straight **12 mm** parallel to the module, then follow an **R38 mm centreline** curve toward the base and out beyond the finger root. It is a remote, broad sweep; the plug is not forced into an immediate elbow to fit a backplate. The holder was opened and the saddle shaped around this route.

The saddle has 0.3 mm nominal envelope clearance and two **1.6 × 3.6 mm tie slots** at X = −8 and +0.8, Y = −42. A loose releasable 2.5 mm tie is shown as a reference envelope; protective sleeve and final tie tension must be established on the real harness. The restraint is about 24 mm longitudinally from the plug exit. Release it before unplugging. Six rear sensor screws release the module toward the grasping gap without removing the root or actuator.

Printed holder and screws clear an **8 mm straight unplug corridor**. A sweep of the conservative full rectangular plug envelope clips **1.315747 mm³** of the vendor sensor's rear housing at jaw Y ≈ −20.398…−19.537, Z = 6.8…7.05. The exact stepped plug was unavailable from the manufacturer download (HTTP 403). The box is not the actual plug, so this does not prove either a real clash or physical removability. Socket placement is left at the measured CAD datum. Actual plug outline, latch and unplug clearance are explicit physical checks; the holder adds no obstruction in that corridor.

The moving lead path is 71.690 mm long. Each external service path is approximately 219.3 mm long at every command, giving about **291 mm combined centreline**, excluding the plug and any upstream cable. Its U-turn has **R25.7 mm** centreline radius; a fixed-end descending turn uses **R25 mm**. The minimum inner envelope radius is **23.1 mm**. As a jaw translates 50 mm, the loop centre translates 25 mm: one straight leg shortens 25 mm and the other lengthens 25 mm. Tangents and endpoints are continuous, with no kink at the moving/service join.

Provisional fixed loom endpoints are base **(−55, 0, 44.681820)** and **(+55, 0, 44.681820)** mm. Suitable external strain relief at these positions is an installation assumption; no actuator holes or fixed-anchor hardware are invented. Horizontal loop portions remain above base Z = 69.181820, over 4.18 mm above the actuator bounding box. Descending tails are at X = ±55, leaving over 10.3 mm outside its X envelope. Full-open cable bounds require approximately **X = ±57.6 and Y = ±138.3 mm**; closed Y extent is ±113.3 mm. Keep this external swept region free of workpieces and nearby equipment. Five complete poses and a continuous separation/constant-length argument cover the supplied gripper; actual cable flex, attachment, rubbing and fatigue remain untested.

**Manufacturer minimum bend radius is unknown.** The inspected Hirose assembly/mating instructions require slack and avoidance of forced bending/tension at the connector but give no numerical minimum. The above radii are generous design assumptions, not manufacturer limits. Actual PaXini harness construction, port selection, cable length, fixed restraints and bend requirement must be confirmed before fabrication/operation. See [primary references](references.md).

## Print assumptions

FDM tolerances are nominal clearance only: zero measured print compensation. Candidate P2S PETG settings are 0.4 mm nozzle, 0.2 mm layers, eight walls and 100% infill. The side print keeps main Y–Z load paths in layers; the short internal core bridges need inspection and support blocking, while exposed features can use removable supports. The 6 mm root gauge verifies only the contact face and pattern. The updated 5.5 mm coupon reproduces the 2.0 mm sensor-head recess and 0.15 mm relief, with one/two/three notches for +0/+0.1/+0.2 mm diameter lanes. The coupon does not reproduce the three long shank stacks or predict full-part stiffness or horizontal-hole fit. See [manufacturing notes](manufacturing.md); no automatic compensation or print release is implied.
