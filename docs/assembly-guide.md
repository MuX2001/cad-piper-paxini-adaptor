# V2 coupon and fit-gauge guide — full print on hold

Read [PRINT-HOLD](../PRINT-HOLD.md). Both sensors are M2324; stock parts remain unmodified. Full adapter files are for digital inspection until the physical gate passes.

## Print preparation

Use the coupon and gauge `_print.stl` files listed in PRINT-HOLD, imported at 1 unit = 1 mm, 100% scale. Bases are at Z=0. Coupon and inner gauge print flat; roof gauge prints with distal Y=2.1 on the bed and builds toward local −Y. Use a brim for the roof's narrow footprint. The [orientation image](../drawings/screenshots/piper_m2324-v2_print_orientation.png) shows this direction on the full roof for review only.

Use the intended printer, nozzle, material and slicer profile; record them. PETG remains a candidate, not a validated material specification. Inspect layer preview for horizontal roof M3 bores/head holes and inner nut-pocket ceilings. Add accessible local supports if needed and record removal. No long cavity bridge is required in this orientation. Coupon vertical holes do not establish horizontal-hole compensation: the roof gauge supplies that directional check.

## Coupon map

Viewed from above, the notch is at −X,−Y. Rows from the notched edge toward +Y have extra offsets **0.00, +0.10, +0.20 mm**. These are experiments, not chosen compensation. The part is 48×30 mm; plate thickness 2.6 mm, nut-test pads 3.6 mm.

| X column | Test | Baseline size / depth |
| --- | --- | --- |
| −18 | M1.6 bore and head | Ø1.8; head Ø3.2 × 1.2 deep |
| −6 | M3 through bore | Ø3.4 |
| +6 | M3 bore and head | Ø3.4; head Ø6.2 × 0.5 deep |
| +18 | M3 nut pocket and through bore | 5.716 across flats × 2.6 deep; Ø3.4 |

Row offset adds to bore/head **diameters** and nut **across-flats** size, not depth. Measure each feature and real hardware; record free fit, hand push, binding, rotation/slop and head seating. Do not force threads through a clearance hole. If no row fits, return that result without scaling the STL or changing the adapter.

## Unpowered gauge fit

1. Record revision, profile, STL hash, units and print settings in the [measurement form](../measurements/m2324-v2-fit-results.md).
2. Disable powered motion. Try inner and roof gauges separately on each finger, then together. Do not scrape/drill stock fingers.
3. Check the distal end wall, visible gaps and complete distal M3 pair. Record bare fit first. The gauge covers only the distal pair of the full design's four bolt positions.
4. Check nuts, bores and heads against the coupon. Lengths are provisional: use the [reach table](m2324-v2-changes.md), measure actual hardware and check protrusion. No torque is specified.
5. If testing removable liners, record upper/lower thickness and compression separately. A snug fit is not a load or slip test.
6. Return the requested measurements/photos and stop. Do not proceed to full printing or powered grasp tests.

Eventual hardware remains eight M3 bolts/nuts and twelve M1.6 sensor screws across both jaws. M1.6 seating/bottoming, selected IN/OUT connector, service loops and full-travel cable paths require confirmation. **30 mm is a conservative software trial floor for later tests, not permission to operate now or a final limit.**
