# Geometric validation — M2324 reference and v2

Digital validation passed on 2026-10-11; **physical validation is pending**. Only coupon and fit gauges are released for unpowered fit tests; see [PRINT-HOLD](../PRINT-HOLD.md). No full-print or operating release is implied.

## Reproduced baseline and environment

Baseline commit: `0d7ee279b727843aca92141fbcb6ef7a688d2cf2`; initially clean worktree. The recreated Python 3.12.3 environment matches all 59 requirements.lock pins, with dependency compatibility and CAD imports passing. Key versions: build123d 0.13.0, OCP 8.0.1.1.0, trimesh 4.12.2, NumPy 2.5.3, Pillow 12.2.0. No system Python packages were installed.

The original source/scripts and exports were copied to `~/workspace/runs/gripper-tac-cad/2026-10-11_m2324-v2/baseline/`, with a read-only-use symlink to supplier assets. Before geometry edits, all four commands passed there:

```bash
python scripts/cad/build_adapter.py --profile m2324-reference
python scripts/cad/build_fit_gauge.py
python scripts/cad/build_assembly.py --opening-mm 50
python scripts/cad/validate_adapter.py
```

Logs: baseline-build-adapter.log, baseline-build-fit-gauge.log, baseline-build-assembly.log and baseline-validation.log in the parent run directory. Existing reference STEP/STL/GLB/PNG files in the project remain untouched. Supplier URDF, finger STL, M2324 STEP and PDF hashes match docs/references.md; no vendor assets were edited.

## Verified CAD and mesh results

V2 uses the four [README commands](../README.md). Machine evidence: `~/workspace/runs/gripper-tac-cad/2026-10-11_m2324-v2/v2-validation.json` and v2-validation.log. JSON records parameters, per-file hashes, metrics and source/vendor hashes; the v2 work is uncommitted, so the input hashes identify it.

| Part | Reference volume mm³ | V2 volume mm³ | V2 export checks |
| --- | ---: | ---: | --- |
| Inner plate | 4988.01 | 4988.01 | PASS |
| Outer roof | 6704.55 | 7122.73 | PASS |
| Inner fit gauge | — | 2267.04 | PASS |
| Roof fit gauge | — | 2566.86 | PASS |
| Fastener coupon | — | 3498.51 | PASS |

PASS means one valid solid after STEP reimport, CAD/export volume agreement within 0.01 mm³, and STL single body, watertight, consistent winding, volume within 1% of CAD. Print-oriented gauge STLs also pass mesh checks and transform back to the original gauge geometry within 0.0001 mm. STL must be imported in **millimetres**, since it has no declared unit.

CAD Boolean intersections are 0 mm³ for sensor/inner, sensor/roof and inner/roof. Reference cavity intrusion is 0 mm³. The inner part is geometrically identical to reference. The six manufactured hole axes stay at X=±8.75, Y=−3.8/−11.8/−19.8; the native vendor axes remain X=±8.75, Y=3/11/19. Sensor rear plane and plate mounting exterior remain Z=−3.2. Sensor Rx180° plus (0,−0.8,−5.35) mm, URDF poses and unit conversions are unchanged.

Both supplied finger meshes were independently checked. Minimum triangle-vertex/axial-section clearances are **0.719 side, 0.511 roof, 0.600 plate** in both profiles. These are piecewise-linear envelope checks on non-watertight source meshes, not physical fit tests. Plane offsets attain their minima at triangle vertices or axial clipping intersections. Distal stop clearance is nominally 0.6 mm.

M3 annular support was checked by exact intersection of complete 2 mm thick bearing rings with all four seats, supplemented by samples (36 azimuths, three radii, depths 0.01/1/2 mm); pocket mouths were checked open. Conservative roof allowance including exterior slope is **2.096 mm**; actual seat-to-split distances are 9.287/7.461 mm. Nominal webs beside nut pockets / below M1.6 head recesses / around tie hole remain 1.2/1.4/1.4 mm. These geometric checks do not establish material strength.

Fit gauges span Y=−10…2.1, retaining the distal taper, 1.5 mm stop wall and both complete distal M3 positions. The proximal interface, lug and stiffness are outside gauge scope.

## Derived assembly envelopes

Each sensor reaches 11.403 mm inward. World sensing normals remain +Y / −Y. Signed Y-envelope gap is command minus 22.805 mm:

| Command opening mm | Paired envelope gap mm |
| ---: | ---: |
| 0 | −22.805 |
| 25 | +2.195 |
| 30 | +7.195 |
| 50 | +27.195 |
| 100 | +77.195 |

Positive separation proves nonintersection of opposing modeled assemblies along Y at those poses. Negative separation identifies an unsafe envelope region, not a calculated penetration volume. Independently posed STL assemblies at 30 mm give +7.195 mm. **30 mm is the conservative software trial floor, not a final limit**; physical testing and cable envelopes may require a larger value.

Clamp and sensor meshes have a **47.002 mm positive Z separation from the base**. Jaw travel only changes world Y, so this separating plane remains valid across 0–100 mm command for these modeled parts. It excludes screws, plugs and cables.

The GLB contains the base, two fingers, four clamshell halves and two supplier sensors at 50 mm command, in metres. Review images: [overall](../drawings/screenshots/piper_dual_m2324-v2_assembly.png), [opposed sensors](../drawings/screenshots/piper_dual_m2324-v2_mount_detail.png), [mounting plane](../drawings/screenshots/piper_m2324-v2_mount_face.png), [section](../drawings/screenshots/piper_m2324-v2_section.png), [M3 seat](../drawings/screenshots/piper_m2324-v2_bearing.png), [print orientation](../drawings/screenshots/piper_m2324-v2_print_orientation.png). Sections are exact thin CAD cuts; rendering uses depth buffering, not simulated hardware.

## Derived liner and print requirements

The rigid cavity has positive clearance; preload requires measured compressible liners. No liner material/hardness/friction coefficient has been assumed. Current upper and lower thicknesses are **unknown**, not zero. For measured t_top/t_bottom, required local compression is t_top+t_bottom minus the vertical clearance below. These are section envelopes, not pointwise contact predictions; curved surfaces and liner placement must be tested.

| Local Y mm | Reference finger width | Reference thickness | Bottom gap | Top gap | Total vertical gap | Total lateral gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| −25 | 30.130 | 9.448 | 1.931 | 0.660 | 2.591 | 1.647 |
| −15 | 27.198 | 8.110 | 1.042 | 1.582 | 2.624 | 1.463 |
| −2 | 21.317 | 7.059 | 0.600 | 1.380 | 1.980 | 3.294 |

Both reference meshes yield these values. Upper/lower liners alone do not establish lateral centering. The previous 0.7–0.8 mm per-side liner suggestion is withdrawn: those thicknesses cannot be assumed to provide preload at these sections. Measure both fingers and return actual compression behavior.

Roof distal-end-down orientation removes the full-width cavity bridge while preserving cavity datums. The external lug ramp has a conservative 41.763° overhang from print vertical. Horizontal M3/head/tie holes and inner nut-pocket ceilings still require slicer review and potentially removable local supports. No slicing or print trial has been performed. Coupon 0/+0.1/+0.2 mm lanes are candidate diameter/across-flats offsets; adapter compensation stays zero. See [screw recalculation and profile differences](m2324-v2-changes.md).

## Still unverified / physical gate

Actual labels, fingers/coatings, upper/lower liners and preload, fastener engagement/protrusion, material/layer strength, torque, slip and tactile performance are unverified. The manual shows IN/OUT connections; intended port, actual plug envelope, service loop, inserted-cable bend space and full-travel route are required. Window and tie lug are retained, but no invented connector is modeled.

The 25 N sensor measurement range is **not** a printed clamp rating. No material model, load/boundary model, FEA or safety factor is supplied. Return the six data groups in PRINT-HOLD and resume before any final interface calibration, cable accommodation, motion limit or full-print recommendation.
