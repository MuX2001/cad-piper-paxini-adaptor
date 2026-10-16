# V2 reach and cable correction audit — 2026-10-16

The existing V2 now places the broad M2324 tactile crown at the original **70.000 mm fingertip reach**, and routes leads parallel to the module before a broad remote bend. This regenerated digital design remains subject to the existing physical print hold. V1 and original vendor assets remain untouched.

[Machine evidence](validation.json) is tied to [source/export hashes](build-manifest.json). The build command in [README](../README.md) regenerates STEP/STL/GLB exports and 15 PNG previews, then runs the geometric checks and both original validators. Exact CAD measurements are in [reference-measurements.json](reference-measurements.json).

Final regeneration and validation completed with **exit code 0**. All 15 previews were visually reviewed. Source/artifact hashes and local documentation links pass the final audit; tracked Git diff is empty. The main STL volume differs from its solid by approximately **0.0032%**.

| Goal requirement | Evidence and limits |
| --- | --- |
| Preserve V1; update existing V2 | 232 original file hashes preserved; user-supplied goal-02 separately protected. No authored files outside V2, no V3; both legacy clamp validators run read-only. |
| Derive reach from original CAD | Both stock fingers measure 70.000 mm from carrier mating plane to distal edge. Distal flat contact band: 59.978–70.000 mm from mount. |
| Move tactile contact to original tip | Three broad sensor crown faces span 51.155–70.000 mm from mount. Distal edge aligns at stock Y = 0; previous V2 reached only 29.398 mm. Housing/holder overhang is excluded from this reach. |
| Reinforce without a large solid holder | Two 3 mm webs with 5 × 3 mm lower flanges and 3 mm curved cross brace; open bays; width 28 mm. Main solid volume approximately 8,729.932 mm³. No strength or deflection rating without material/load evidence. |
| Opposing faces and useful opening | Actual sensor normals map to base +Y/−Y. Conservative opposed gap is command + 1.994608484 mm over command 0–100 mm. |
| Correct parallel cable exit | Proximal socket mouths measured at native X ±3.6, Y 18.520260 with +Y exit normal. Selected left port maps to jaw −Y. Straight 12 mm lead run precedes an R38 mm centreline sweep. |
| Strain relief and service access | Open saddle with two 1.6 × 3.6 mm slots and releasable tie away from plug. Six sensor screw/tool paths clear; holder and screws clear 8 mm straight plug-withdrawal corridor. Real plug/latch access is unverified, as detailed below. |
| Travel and cable slack | 71.690 mm moving path plus 219.309 mm service path; 290.999 mm combined per side. Fixed endpoints, continuity and constant length checked at 101 positions. R25.7 U-turn translates 25 mm for 50 mm jaw travel; R25 fixed-end turn. |
| Full motion | Continuous pure-translation separation for rigid parts. Five configurations at 0/25/50/75/100 check service loops against both jaws, carriers, sensors, screws, ties and conservative actuator box. Loops above base; descending tails outside its X bounds. Assumes harness follows proposed route. |
| Cable space and bend assumptions | Full-open cable region X ±57.6, Y ±138.3 mm; provisional fixed loom ends (±55, 0, 44.682) mm. Minimum inner envelope radius 23.1 mm. Manufacturer minimum radius and actual harness/sleeve dimensions unknown. |
| Mounting and fasteners | Both 504-triangle carriers and four-hole 12 × 8 pattern retained; six sensor axes match STEP. Candidate root/sensor penetration 2.0/1.4 mm; sensor bearing annuli and tool paths checked. Real threads/depth unverified. |
| Printable solids | Finger, gauge and coupon each reimport as one valid STEP solid and watertight STL body. Proper print transforms and bed Z = 0 checked. Main print envelope 22.5 × 73.2 × 28 mm; accessible supports required. |
| Complete assemblies | Full GLBs at 0/50/100 contain 35 named components, including unchanged actuator mesh and cable route; vertices, triangles and poses checked after reimport. Six-solid finger/sensor/carrier STEP and eight-solid cable STEP verified separately. |
| Requested previews | Common-datum side comparison, rear cable route, side exit, open/closed and isometric assembly, service loops and print orientation rendered from the same geometry. |

Key views: [reach comparison](../drawings/reach_comparison.png), [rear cable route](../drawings/cable_routing.png), [side exit](../drawings/cable_exit_side.png), [closed](../drawings/assembly_open0.png), [open](../drawings/assembly_open100.png), [isometric](../drawings/assembly_open50.png), [print orientation](../drawings/print_orientation.png).

The conservative rectangular plug is clear while mated. During straight withdrawal its maximal box clips **1.315747 mm³ of the vendor sensor housing**; printed holder and screws remain clear. The actual stepped plug was not supplied and its public download returned HTTP 403. This is an unresolved plug-shape/latch check, not verified physical unmating. No sensor or connector CAD is moved to hide the uncertainty.

The [physical checklist](../measurements/fit-checklist.md) records remaining thread, screw, harness, bend-radius, fixed-restraint, print-compensation and load checks. Cable envelopes are not dynamic flex/fatigue simulations. No slicing, full printing, force/torque test or powered gripper command was performed. [PRINT-HOLD.md](../../PRINT-HOLD.md) remains in force.
