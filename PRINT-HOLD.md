# PRINT HOLD — physical fit data required

Only these `cad/exported/` files are released for **unpowered fit tests**, imported as millimetres:

- `piper_m2324-v2_fastener_coupon.stl` — flat base on bed.
- `piper_m2324-v2_fit_gauge_inner_print.stl` — mounting face on bed.
- `piper_m2324-v2_fit_gauge_roof_print.stl` — distal end on bed; use a brim.

Do not print the full adapter yet. Its STEP/STLs and GLB are for digital review. Inspect small-hole and nut-pocket support needs in the slicer; see the [guide](docs/assembly-guide.md). Do not force gauges onto either finger or permanently modify it.

Return these results using the [measurement form](measurements/m2324-v2-fit-results.md):

1. Inner/roof gauge fit on **each** finger: tightness, visible gaps, distal stop and M3 alignment.
2. Each finger's width, thickness and surface condition at local Y = −25, −15, −2 mm.
3. Coupon fits for M3 nuts, M3 bores, screw-head pockets and M1.6 bores, with tested lane and print settings.
4. Actual upper/lower liner thicknesses, material and compression behavior.
5. Photos of both M2324 labels, mounting backs, plugs and cables; identify intended IN/OUT port.
6. Minimum bending space with the actual cable inserted, service loop and proposed route throughout travel.

Stop at this physical gate. Only after these data arrive and the Goal is resumed may cavity/print compensation, liners, cable clearance, minimum opening and full-print release be finalized. **30 mm is a conservative software trial floor, not a final limit.** No physical fit, load, torque or cable test has been completed.
