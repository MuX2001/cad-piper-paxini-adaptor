# V2 PETG / P2S acceptance — 2026-10-16

**CAD VALIDATED for the reference geometry. Not SLICE VERIFIED, not PHYSICALLY VALIDATED, not print-ready.**

Baseline: PETG, 0.4 mm nozzle, 0.20 mm layers, 4–5 walls, 25–35% infill. These are evaluation settings, not a tested process. [Machine evidence](printability-acceptance.json) records exact STL hashes and the build manifest; [assembly evidence](validation.json) and the [six-screw audit](sensor-screw-access.md) supply the CAD checks.

| Check | Result | Evidence |
| --- | --- | --- |
| Mesh integrity | **PASS** | All 6 current STLs: single closed manifold surface, consistent winding, no degenerate/duplicate faces or improper triangle intersections; exact file hashes recorded. |
| Minimum dimensions | **PASS** | Solid arm replaces the enclosed cell; preserved 5 mm web bands and 6 mm root seats. Continuous 3.6 mm screw plate / 3 mm electronics floor; interface exceptions documented. |
| Overhangs and bridging | **NOT VERIFIED** | No slicer. Enclosed core and isolated pad starts removed; common-pocket closure still exceeds the 10 mm bridge screen. Actual toolpaths remain unknown. |
| Support accessibility | **NOT VERIFIED** | Common pocket and root service opening are open to removal tools. No enclosed core remains. Actual generated support accessibility has not been inspected. |
| Mounting and sensor compatibility | **PASS** | Reference CAD: unchanged PiPER axes, 17.5 x 8 sensor pattern, sensor plane/reach and cable route; S1-S6 insertion/seat/tool/removal PASS. Actual hardware and plug latch fit remain unverified. |
| Structural orientation | **PASS** | Finger X=-14 side down: longitudinal Y and dominant Y-Z grip bending remain in the layer plane, including the root. No quantified printed strength claim; lateral/torsional loading is unvalidated. |
| PETG slicing | **NOT VERIFIED** | No compatible slicer executable/application found; no toolpath, filament/time estimate or slicer-native project. |

## Mesh evidence

Six active STL files = three printable components in native and print placements. Imported vendor meshes, assembly visualization meshes and historical revisions are not current printable exports. All six were checked individually, without mesh repair. Every edge has exactly two incident faces and every vertex has a single manifold fan. Finite coordinates, positive volume, consistent winding, single surface, duplicate and zero-area faces were checked. Triangle intersections were checked explicitly, including coplanar overlaps; legitimate common-edge/vertex contact is excluded. Numerical contact tolerance is 0.000001 mm; plane zero tolerance is 0.0000000001 mm. Nine analytic crossing/contact/separation cases passed. These are mesh checks, not a guarantee that slicing retains every hole.

| STL | Triangles | Connected surfaces | Improper intersections | Result |
| --- | ---: | ---: | ---: | --- |
| `fastener_coupon.stl` | 2904 | 1 | 0 | PASS |
| `fastener_coupon_print.stl` | 2904 | 1 | 0 | PASS |
| `mount_fit_gauge.stl` | 1712 | 1 | 0 | PASS |
| `mount_fit_gauge_print.stl` | 1712 | 1 | 0 | PASS |
| `replacement_finger.stl` | 12508 | 1 | 0 | PASS |
| `replacement_finger_print.stl` | 12508 | 1 | 0 | PASS |

## Dimensions and simplification

The enclosed arm cell is filled. Actual normal depth at nine middle-arm probes is at least **13.711 mm**; the old 3.5 mm skin bands are contained within that solid material. The preserved outside web bands measure **5.000 mm** and root screw-bearing stacks **6.000 mm**. Exact root-region comparison and actual arm sections are recorded in [the section comparison](mechanical-comparison.md). The current STEP and parametric source have zero difference in both valid boolean directions.

- The unchanged root service opening leaves local 4 mm side walls for screw/key and cable access. Main web bands remain at least 5 mm; all root bearing stacks remain 6 mm.
- Sensor interface: 3.6 mm screw-bearing plate, 3.0 mm floor over electronics, 3.0 mm outer rails and 2.0 mm distal pocket rim. These local dimensions preserve short screws and open access, with a continuous supported plate instead of separate pads.
- The shallow underside electronics relief retains its existing 1.5 mm end land over only 0.6 mm depth. This is an interface edge backed by the continuous 3 mm plate, not an isolated thin rim.
- The 3 mm radial cable saddle and 1.6 x 3.6 mm tie slots retain the established cable route and strain relief. This saddle is a cable interface, not the primary arm skin.
- The 0.15 mm bore-mouth chamfer and R0.4 pocket-floor blend are seating reliefs, not thin protrusions. Coupon identification lands remain at least 1.6 mm.

All six sensor seats are Z=12.8 above the fixed Z=9.2 sensor plane: **3.6 mm pass-through**, no counterbore, candidate **M1.6×5**, head Ø3 × 1.6, hex 1.5. Nominal penetration is 1.4 mm into the specified 2 mm depth; the stated screw-length/print-stack sensitivity leaves 0.21 mm depth margin. Driver radial clearance is 0.75 mm nominal, 0.60 mm under the stated undersize case. Actual screws, tool details, usable threads and printed fit remain UNVERIFIED.

## Orientation and outstanding slicing

- **replacement_finger:** Existing print STL: native X=-14 on bed; footprint 27 x 73.2, height 28. Dominant bending in layer plane.
- **mount_fit_gauge:** Native Y=-70 mating face on bed; footprint 28 x 22.5, height 6; all bores vertical. An unpowered fit gauge, not a load-bearing finger.
- **fastener_coupon:** Flat XY base on bed; 36 x 18, height 3.6; all fit holes and identification cuts vertical. An unpowered fit coupon.

Side-down printing keeps longitudinal Y and dominant Y-Z gripping-plane bending within layers through the root. Lateral/torsional loads and local joints remain physically unvalidated; no strength is inferred from infill settings.

The six isolated pad starts and enclosed arm core have been eliminated. The single open pocket has a **17.7 mm straight closure span** between its rounded ends, above the conservative 10 mm bridge screen. Use accessible support on its X-facing upper wall unless the slicer validates the bridge. Support can be reached through the broad +Z pocket opening; keep its Z-facing head seats and sensor-contact plane free of support. Root service opening, rear cable channel and horizontal bores also need layer inspection. The [print orientation preview](../drawings/print_orientation.png) identifies the support-review region, not generated supports.

No compatible slicer is available in the recorded locations. **Slicer project, generated support accessibility, print time, filament usage and retention of holes after slicing: NOT VERIFIED.** Selected CAD sections do not substitute for slicer layers. No full-print release is granted; [PRINT-HOLD](../../PRINT-HOLD.md) and the [fit checklist](../measurements/fit-checklist.md) remain in force.
