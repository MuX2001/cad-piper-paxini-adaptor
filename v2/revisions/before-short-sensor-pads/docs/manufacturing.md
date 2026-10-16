# Reinforced V2 — P2S / PETG manufacturing and assembly

The digital part is one solid with a **27 × 73.2 mm bed envelope and 28 mm height** in `replacement_finger_print.stl`. Import STL as millimetres. The existing full-print hold remains; these are process candidates, not slicer or print-test results.

## Section sizes and orientation

| Feature | Nominal dimension / significance |
| --- | --- |
| Main side webs | 5 mm; locally 4 mm beside the root service opening |
| Front / rear skins | 3.5 mm vertically; approximately 3.43 mm normal to the sloped rear wall |
| Root bearing seat | 6 mm, with complete Ø3.8/Ø2.4 head-bearing annuli; deeper collar supports the seat |
| Sensor rails / head bosses | Original sloping rails retained; Ø7.2 pads, Ø4.2 × 2 mm pockets; 1.5 mm radial rim; minimum floors 6 / 10 / 14 mm |
| Sensor screw seating relief | Six 0.15 × 45° chamfers, Ø2.1→Ø2.4 at the bore mouth; seats Z=15.8 / 19.8 / 23.8 |
| Stress-relieving geometry | R2.5 outer transitions, R2 internal core fillets, R3 service-opening corners |
| Cable saddle / tie slots | 3 mm saddle; 1.6 × 3.6 mm slots for a releasable 2.5 mm tie; no rear-skin perforation |

The **X=−14 side lies on the bed**. Layer normal is jaw X; longitudinal Y fibres and the gripping-plane Y–Z load path lie within layers. This favours the dominant bending load. Lateral and torsional loads still depend on interlayer shear and bonding; neither is certified by the beam calculation. Do not rotate the finger upright on its root simply to hide support needs.

Candidate settings: **0.4 mm nozzle, 0.2 mm layers, eight walls, 100% infill**, dry PETG and the appropriate profile for the actual filament. The fully dense geometry is the basis of the comparative mass and section calculations. Using sparse infill requires a new stiffness assumption. Temperature, cooling, speed, extrusion and drying settings must follow the chosen filament/profile and be recorded; no specific PETG grade has been physically confirmed.

## Bridges, supports and finishing

The enclosed core is 18 mm wide along the build direction, but its closing roof bridges across the smaller **Z gap, nominally at most 12 mm**. The R2 corners shorten the actual closing-layer spans. Keep automatic supports out of this core; inspect the layer preview for a continuous short bridge and adequate anchoring. It communicates with the root service opening, but relying on dense trapped supports would make removal difficult. Bridge quality still needs a coupon/profile check before the full-print hold is lifted.

Use accessible removable supports where the exposed sensor-window lip, saddle and horizontal holes require them. The central sensor opening and root service window permit tool access; avoid bonding support to the sensor seating strips or root datum. Do not thin the webs to remove every overhang. Inspect the side-down layers around the sensor bosses, counterbored head pockets and 1.6 mm tie slots. Remove only process residue; do not enlarge load-bearing openings or uniformly scale the part to correct hole fit.

Nominal clearances are Ø2.4 for M2 shafts, Ø4.2 for assumed Ø3.8 root heads, **Ø2.1 for M1.6 shafts and Ø4.2 for sensor heads/drivers**. No measured shrink compensation is applied. The existing 5.5 mm coupon body now has the **2 mm shallow counterbore and 0.15 mm seating chamfer**, in +0/+0.1/+0.2 mm diameter lanes. It checks local pocket/bore fit, not the three long shank stacks. The 6 mm root gauge checks the attachment pattern.

The [six-screw audit](sensor-screw-access.md) verifies **0.60 mm nominal radial driver clearance**; a declared 0.30 mm diametric hole-undersize case still leaves **0.45 mm**. It also bounds the Ø3.14 knurled head and the maximum under-head blend. The ±0.15 mm stack-error case retains positive margin to nominal sensor depth. These are design allowances requiring calibration, not demonstrated PETG precision. Measure roundness, hole position, shoulder flatness and actual screw protrusion after accessible support removal; do not force a screw into an undersized printed bore. Keep the structurally supported bearing annulus and remove only process residue.

The 8/12/16 mm sequence uses documented catalog sizes. Raising the local seats accommodates these lengths and keeps every head pocket 2 mm deep, without cutting down the sloping rails. The net added solid volume is 989.783 mm³, approximately 1.27 g at the comparison density.

## Assembly and servicing

1. Verify real carrier threads, head types and usable depth. Retain each stock finger whole. No actuator or transmission modification is required by the model.
2. Fit each replacement using four candidate **M2×8** screws. The 6 mm seat retains 2 mm nominal penetration. Insert heads through the rounded root service opening. A short L-key with a Ø2.4 clearance envelope has a checked **60° inward turn**; the actual hex size and tool fit remain unverified. Fit root screws before sensors and harness.
3. Seat each M2324 on the unchanged rear strips without forcing it. Fit candidate **M1.6×8 at S1/S4, M1.6×12 at S2/S5 and M1.6×16 at S3/S6**, from distal to proximal. All have 2 mm counterbores and 1.4 mm nominal penetration. Keep lengths segregated; a longer screw in a shorter stack can bottom in the sensor. The modeled 1.5 mm hex screwdriver reaches all six directly with 0.7 mm nominal socket engagement. No tightening torque is assigned.
4. Mate the DF53 plug along the sensor plane. Route leads through the open service/cable channel, preserving the 12 mm straight run and R38 sweep. Add a protective sleeve and releasable tie at the saddle. The cable is not trapped inside the closed cell. Arrange the unchanged generous service loops and provisional fixed loom restraints.
5. To remove a sensor, use adequate unpowered jaw separation, release its tie and plug, undo six rear screws and move the module toward the gap. A 12 mm conservative sensor-envelope removal sweep clears the holder. The root remains assembled. The pre-existing conservative plug-box/vendor-housing withdrawal overlap and real latch ergonomics remain physical checks.

Before full printing or operation, follow the existing [physical checklist](../measurements/fit-checklist.md) and [PRINT-HOLD](../../PRINT-HOLD.md). Record the source manifest, filament, settings, support strategy, fit and measured deflection. Required operating force, allowable deflection, preload, creep, cyclic endurance and real cable motion are still unverified. The comparative beam calculation supplies no allowable load or fatigue life.
