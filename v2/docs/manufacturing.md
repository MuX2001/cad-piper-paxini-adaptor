# V2 PETG / P2S manufacturing and assembly

**CAD geometry only; slicing and physical validation are pending.** The existing [PRINT-HOLD](../../PRINT-HOLD.md) is unchanged. Use the [acceptance evidence](printability-acceptance.md) for the exact active export hashes and results.

| Component | Print placement | Size / role |
| --- | --- | --- |
| Replacement finger | Native X=−14 side on bed; use `_print.stl` | 27 × 73.2 mm footprint, 28 mm height; quantity 2 |
| Mount fit gauge | Native Y=−70 mating face on bed | 28 × 22.5 mm footprint, 6 mm height; unpowered interface check |
| Fastener coupon | Flat XY base on bed | 36 × 18 mm footprint, 3.6 mm height; vertical clearance-hole lanes |

Import STL as millimetres. The user evaluation baseline is Bambu Lab P2S, PETG, 0.4 mm nozzle, 0.20 mm layers, 4–5 walls and 25–35% infill. Actual PETG grade and slicer profile are unspecified. No additional process requirements or automatic print compensation are introduced.

Side printing keeps the long Y direction and dominant Y-Z bending load path within layers, including the root. The primary arm is now solid CAD geometry, retaining the earlier skin/web bands and root collar. Lateral/torsional loads, bolted joints and material creep remain unvalidated; infill does not establish a strength rating.

The common open sensor pocket has a 17.7 mm straight wall-closure span, above the conservative 10 mm bridge screen. Review accessible support on the X-facing upper pocket wall, or validate the bridge in the slicer. The +Z opening gives removal access. Keep support off Z-facing screw-head seats and sensor-contact strips. Root service opening, rear cable channel and horizontal bores also need layer inspection. The enclosed arm core and six isolated pad starts have been eliminated. The [orientation preview](../drawings/print_orientation.png) marks a support-review area, not generated supports. No compatible slicer is available: layer inspection, hole retention, actual support removability, filament usage, print time and slicer project are NOT VERIFIED.

Candidate pair hardware is 8 × M2×8 root screws and 12 × M1.6×5 sensor screws. Root M2 threads remain inferred from the source mesh. The M2324 manual specifies six M1.6 threaded holes, 2 mm depth. The sensor plate is 3.6 mm thick at all heads, leaving 1.4 mm nominal penetration; a 6 mm screw is too long. Reference screw head Ø3 × 1.6, 1.5 mm hex; practical reference driver Ø3 shaft / 60 mm blade. Actual screws, tip/handle and allowable torque are unconfirmed. [Per-screw check](sensor-screw-access.md).

Assembly sequence: verify the stock interface, retain the removed stock fingers, attach each replacement through its root service opening using the checked short L-key envelope, then install sensor screws from the common rear pocket and route the harness. Release the tie and unplug before sensor removal. All six screw paths remain accessible with the root attached; the sensor withdraws toward the grasping gap. Actual plug latch/outline must be checked because its conservative box sweep intersects the vendor sensor housing, although the finger clears the corridor.

Record actual coupon clearances, stack and screw protrusion before assembly. The 0.15 mm radial undersize and ±0.15 mm stack error are sensitivity assumptions, not calibrated PETG capabilities. Under that case driver clearance is 0.60 mm and the combined screw-length/stack envelope retains 0.21 mm to nominal sensor depth. Fully formed thread engagement and safe torque require physical confirmation. [Fit checklist](../measurements/fit-checklist.md).
