# Geometric validation — paired M2324 reference

Run on 2026-10-11 with Python 3.12.3, build123d 0.13.0, trimesh 4.12.2, NumPy 2.5.3, and the supplied vendor assets. The directory has no Git repository, so there is no commit identifier. The CAD build is deterministic and uses no random seed.

Commands from the project root:

```bash
python scripts/cad/build_adapter.py --profile m2324-reference
python scripts/cad/build_fit_gauge.py
python scripts/cad/build_assembly.py --opening-mm 50
python scripts/cad/validate_adapter.py
```

Both manufactured STEP files reimport as one valid solid each. The inner plate is 4,988.01 mm³ and the outer roof with cable lug is 6,704.55 mm³. Both exported STLs are single-body, watertight, and consistently wound; their mesh volumes agree with the CAD solids within 1%. The two fit-gauge STLs are also single-body and watertight.

The gripper finger STL, interpreted in millimetres after the URDF/DAE metre conversion, stays inside the modeled clamp cavity. Minimum sampled/section clearances are 0.719 mm to a side, 0.511 mm to the roof, and 0.600 mm to the inner plate. The imported M2324 STEP has six cylindrical mounting axes at X = ±8.75 mm and Y = 3/11/19 mm. Exact CAD intersections give 0 mm³ overlap between sensor and each clamp part, and between the clamp halves. Minimum nominal material webs are 1.2 mm beside the M3 nut pockets, 1.4 mm beneath the M1.6 head recesses, and 1.4 mm around the cable-tie hole.

Each assembled sensor extends 11.403 mm into the nominal closed jaw gap. The paired-jaw Y-envelope separation is **−22.805 mm at 0 mm command**, +0.195 mm at 23 mm, +1.195 mm at 24 mm, +2.195 mm at 25 mm, +27.195 mm at 50 mm, and +77.195 mm at 100 mm. The active-face normals point in opposite world-Y directions toward each other. Positive separation along Y proves no opposing-jaw CAD collision for the checked configurations at or above 23 mm; **25 mm is the provisional operating floor** to leave more than 2 mm nominal envelope clearance. An independent check of the posed finger, clamp, and sensor STL meshes at 25 mm confirms the +2.195 mm Y-envelope gap. The clamp and sensor envelope begins about 47 mm above the gripper-base mesh. The interactive GLB includes the stock base, both fingers, four clamp parts, and two supplied sensor references at a 50 mm command; PNG views were inspected.

**Limits:** The stock finger mesh contains open, non-watertight components, so these checks use its triangle envelope and do not prove a physical contact fit or structural strength. Negative envelope separation at full closure indicates an unsafe operating region, but is not a precise penetration volume. The sensor-to-adapter intersection check does not verify screw thread fit, preload, cable plug clearance, or sensing performance. Cable plugs and service loops are absent from the CAD assembly. The first-pass load discussion in [design-rationale.md](design-rationale.md) is not a structural test. The physical M2324 units and both fingers have not been measured. No printed or physical test has been performed.
