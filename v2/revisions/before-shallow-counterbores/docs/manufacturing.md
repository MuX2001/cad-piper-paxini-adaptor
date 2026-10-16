# Reinforced V2 — P2S / PETG manufacturing and assembly

The digital part is one solid with a **27 × 73.2 mm bed envelope and 28 mm height** in `replacement_finger_print.stl`. Import STL as millimetres. The existing full-print hold remains; these are process candidates, not slicer or print-test results.

## Section sizes and orientation

| Feature | Nominal dimension / significance |
| --- | --- |
| Main side webs | 5 mm; locally 4 mm beside the root service opening |
| Front / rear skins | 3.5 mm vertically; approximately 3.43 mm normal to the sloped rear wall |
| Root bearing seat | 6 mm, with complete Ø3.8/Ø2.4 head-bearing annuli; deeper collar supports the seat |
| Sensor rails / head bosses | 5.5 mm rails, Ø6 bosses, Ø3.2 pockets; 1.4 mm radial boss rim; 2.6 mm material below screw seat |
| Sensor screw seating relief | Six 0.15 × 45° chamfers, Ø1.8→Ø2.10 at the bore mouth; flat seat Z=11.8 retained |
| Stress-relieving geometry | R2.5 outer transitions, R2 internal core fillets, R3 service-opening corners |
| Cable saddle / tie slots | 3 mm saddle; 1.6 × 3.6 mm slots for a releasable 2.5 mm tie; no rear-skin perforation |

The **X=−14 side lies on the bed**. Layer normal is jaw X; longitudinal Y fibres and the gripping-plane Y–Z load path lie within layers. This favours the dominant bending load. Lateral and torsional loads still depend on interlayer shear and bonding; neither is certified by the beam calculation. Do not rotate the finger upright on its root simply to hide support needs.

Candidate settings: **0.4 mm nozzle, 0.2 mm layers, eight walls, 100% infill**, dry PETG and the appropriate profile for the actual filament. The fully dense geometry is the basis of the comparative mass and section calculations. Using sparse infill requires a new stiffness assumption. Temperature, cooling, speed, extrusion and drying settings must follow the chosen filament/profile and be recorded; no specific PETG grade has been physically confirmed.

## Bridges, supports and finishing

The enclosed core is 18 mm wide along the build direction, but its closing roof bridges across the smaller **Z gap, nominally at most 12 mm**. The R2 corners shorten the actual closing-layer spans. Keep automatic supports out of this core; inspect the layer preview for a continuous short bridge and adequate anchoring. It communicates with the root service opening, but relying on dense trapped supports would make removal difficult. Bridge quality still needs a coupon/profile check before the full-print hold is lifted.

Use accessible removable supports where the exposed sensor-window lip, saddle and horizontal holes require them. The central sensor opening and root service window permit tool access; avoid bonding support to the sensor seating strips or root datum. Do not thin the webs to remove every overhang. Inspect the side-down layers around the sensor bosses, counterbored head pockets and 1.6 mm tie slots. Remove only process residue; do not enlarge load-bearing openings or uniformly scale the part to correct hole fit.

Nominal clearances are Ø2.4 for M2 shafts, Ø4.2 for assumed Ø3.8 root heads, Ø1.8 for M1.6 shafts and Ø3.2 for catalog-reference plain Ø3.0 sensor heads. Print compensation is zero. The updated 5.5 mm coupon checks the sensor head stack and 0.15 mm seating chamfer; the 6 mm root gauge checks the attachment pattern. Coupons do not certify horizontal-hole compensation, strength, flatness or full-part fit. The [six-screw audit](sensor-screw-access.md) finds only 0.0354 mm nominal free clearance at the maximum under-head blend and 0.100 mm radial driver clearance. Confirm these on the actual print and hardware. A knurled Ø3.14 head would leave only 0.030 mm radial clearance; do not treat head styles as interchangeable.

## Assembly and servicing

1. Verify real carrier threads, head types and usable depth. Retain each stock finger whole. No actuator or transmission modification is required by the model.
2. Fit each replacement using four candidate **M2×8** screws. The 6 mm seat retains 2 mm nominal penetration. Insert heads through the rounded root service opening. A short L-key with a Ø2.4 clearance envelope has a checked **60° inward turn**; the actual hex size and tool fit remain unverified. Fit root screws before sensors and harness.
3. Seat each M2324 on the unchanged rear strips without forcing it. Fit six candidate **M1.6×4** screws from the rear. The 2.9 mm recess in 5.5 mm rails preserves the original Z=11.8 screw seat and 1.4 mm nominal engagement. No tightening torque is assigned.
4. Mate the DF53 plug along the sensor plane. Route leads through the open service/cable channel, preserving the 12 mm straight run and R38 sweep. Add a protective sleeve and releasable tie at the saddle. The cable is not trapped inside the closed cell. Arrange the unchanged generous service loops and provisional fixed loom restraints.
5. To remove a sensor, use adequate unpowered jaw separation, release its tie and plug, undo six rear screws and move the module toward the gap. A 12 mm conservative sensor-envelope removal sweep clears the holder. The root remains assembled. The pre-existing conservative plug-box/vendor-housing withdrawal overlap and real latch ergonomics remain physical checks.

Before full printing or operation, follow the existing [physical checklist](../measurements/fit-checklist.md) and [PRINT-HOLD](../../PRINT-HOLD.md). Record the source manifest, filament, settings, support strategy, fit and measured deflection. Required operating force, allowable deflection, preload, creep, cyclic endurance and real cable motion are still unverified. The comparative beam calculation supplies no allowable load or fatigue life.
