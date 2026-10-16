# Reinforced V2 — P2S / PETG manufacturing and assembly

The digital part is one solid with a **27 × 73.2 mm bed envelope and 28 mm height** in `replacement_finger_print.stl`. Import STL as millimetres. The existing full-print hold remains; these are process candidates, not slicer or print-test results.

## Section sizes and orientation

| Feature | Nominal dimension / significance |
| --- | --- |
| Main side webs | 5 mm; locally 4 mm beside the root service opening |
| Front / rear skins | 3.5 mm normal thickness; rear inner roof offset 3.573738 mm vertically |
| Root bearing seat | 6 mm, with complete Ø3.8/Ø2.4 head-bearing annuli; deeper collar supports the seat |
| Sensor flanges / access | 6 × 6 mm short flanges; 3.6 mm effective stack, 3.0 mm minimum lip; 4.5 mm open U pockets |
| Sensor screw seating relief | Six 0.15 × 45° chamfers, Ø2.1→Ø2.4 at the bore mouth; all six seats Z=12.8 |
| Stress-relieving geometry | R2.5 outer transitions, R2 internal core fillets, R3 service-opening corners |
| Cable saddle / tie slots | 3 mm saddle; 1.6 × 3.6 mm slots for a releasable 2.5 mm tie; no rear-skin perforation |

The **X=−14 side lies on the bed**. Layer normal is jaw X; longitudinal Y fibres and the gripping-plane Y–Z load path lie within layers. This favours the dominant bending load. Lateral and torsional loads still depend on interlayer shear and bonding; neither is certified by the beam calculation. Do not rotate the finger upright on its root simply to hide support needs.

User evaluation baseline: **PETG, 0.4 mm nozzle, 0.20 mm layers, 4–5 wall loops, 25–35% infill**. Prefer adequate walls to increasing infill for reinforcement. This supersedes the earlier eight-wall/100% suggestion and is not a tested process profile. The fully solid geometry remains the basis of the comparative mass and beam calculations; those results do not predict this sparse-infill print's mass or stiffness. Actual filament settings remain unspecified. See the [acceptance report](printability-acceptance.md).

## Bridges, supports and finishing

The enclosed core is 18 mm wide along the build direction. Its nominal vertical gap reaches **11.926 mm**, exceeding the conservative 10 mm bridge screen. R2 corners reduce closure spans, but actual bridge direction, anchoring and toolpaths are **NOT VERIFIED**. The core communicates with the root service opening; removal of generated internal supports has not been demonstrated. Do not treat a support blocker as proof that the bridge will print.

The [CAD build sections](../drawings/printability_sections.png) show three positive-X sensor-pad lips starting near print Z=19.9 mm without material directly below. They need support through the open central window or another validated toolpath strategy. Their X-facing sides are candidate support-contact surfaces, leaving the sensor plane and head seats clear; accessibility and removal still require slicer review. Inspect the saddle, horizontal holes, root window, U pockets and tie slots as well. These CAD sections are not slicer layers. No compatible slicer was found, so support accessibility, hole retention after slicing, filament usage and print time are **NOT VERIFIED**.

The root gauge prints on its Y=-70 mating face, 28 × 22.5 mm footprint and 6 mm high; its bores are vertical. The coupon prints flat, 36 × 18 × 3.6 mm, with vertical holes and identification cuts. Coupon notch lands now measure 1.6 mm. Neither requires above-bed overhangs in the CAD mesh screen; both still need actual slicing. The finger's 4 mm service-opening walls, 3 mm sensor lips/rails and 1.5 mm distal sensor-window rim are documented interface exceptions in the acceptance report. Main webs, normal skins and root seats meet 5 / 3.5 / 6 mm.

Nominal clearances remain Ø2.4 for M2 shafts and Ø4.2 for assumed Ø3.8 root heads. Sensor shank holes are **Ø2.1**, and their **4.5 mm wide open U pockets** provide **0.75 mm radial clearance** for the reference Ø3 mm driver. No measured shrink compensation is applied. The existing coupon now has a **3.6 mm body**, reproducing the actual screw pass-through and 0.15 mm bore-mouth relief, in +0/+0.1/+0.2 mm diameter lanes. The separate 6 mm root gauge remains unchanged.

The [six-screw audit](sensor-screw-access.md) checks a stated 0.30 mm diametric hole/pocket undersize case; driver clearance remains **0.60 mm**. The maximum head and under-head blend still clear. Combining an assumed ±0.15 mm stack error with the 5 mm screw's length tolerance leaves **0.21 mm** to nominal sensor depth. These are allowances requiring calibration, not demonstrated PETG accuracy. Measure roundness, hole position, shoulder flatness and actual protrusion after support removal; retain the supported bearing annulus and remove only process residue.

All six screws are the same **M1.6×5**, avoiding row-specific lengths. The flat head seats are only **3.6 mm from the sensor plane**. U-shaped access opens into the sensor window, allowing support removal and direct access without long enclosed tunnels. R0.4 pocket floors soften local transitions; the root/arm reinforcement and continuous 3 mm outer rails are preserved. The one-piece part remains valid, so no removable plate or additional fasteners were introduced.

## Assembly and servicing

1. Verify real carrier threads, head types and usable depth. Retain each stock finger whole. No actuator or transmission modification is required by the model.
2. Fit each replacement using four candidate **M2×8** screws. The 6 mm seat retains 2 mm nominal penetration. Insert heads through the rounded root service opening. A short L-key with a Ø2.4 clearance envelope has a checked **60° inward turn**; the actual hex size and tool fit remain unverified. Fit root screws before sensors and harness.
3. Seat each M2324 on the unchanged rear strips without forcing it. Fit **six M1.6×5 reference screws** from the rear onto the flat Z=12.8 pads. Each 3.6 mm pass-through gives 1.4 mm nominal penetration into the specified 2 mm holes. Do not substitute a 6 mm screw. The modeled 1.5 mm hex screwdriver reaches every seat through the open U pockets with 0.7 mm nominal socket engagement. Actual usable threads and permissible tightening torque remain unverified.
4. Mate the DF53 plug along the sensor plane. Route leads through the open service/cable channel, preserving the 12 mm straight run and R38 sweep. Add a protective sleeve and releasable tie at the saddle. The cable is not trapped inside the closed cell. Arrange the unchanged generous service loops and provisional fixed loom restraints.
5. To remove a sensor, use adequate unpowered jaw separation, release its tie and plug, undo six rear screws and move the module toward the gap. A 12 mm conservative sensor-envelope removal sweep clears the holder. The root remains assembled. The pre-existing conservative plug-box/vendor-housing withdrawal overlap and real latch ergonomics remain physical checks.

Before full printing or operation, follow the existing [physical checklist](../measurements/fit-checklist.md) and [PRINT-HOLD](../../PRINT-HOLD.md). Record the source manifest, filament, settings, support strategy, fit and measured deflection. Required operating force, allowable deflection, preload, creep, cyclic endurance and real cable motion are still unverified. The comparative beam calculation supplies no allowable load or fatigue life.
