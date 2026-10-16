# Previous versus reinforced V2

Baseline: `fe94d0548cd070a5a3ab135652aff9194e426492`; all 47 previous V2 files retained in `../revisions/goal-02/` and checked against `previous-revision.json`.

| Metric | Previous V2 | Reinforced V2 |
| --- | ---: | ---: |
| Width × length × depth | 28 × 73.2 × 22.5 mm | 28 × 73.2 × 27 mm |
| Tactile reach from original mount | 70.000 mm | 70.000 mm |
| Solid-material mass estimate, same density | 11.17 g | 28.47 g |
| Root bearing thickness / nominal engagement | 4 / 2 mm, M2×6 | 6 / 2 mm, M2×8 |
| Web / skin / sensor rail minimum | 3 / open / 4 mm | 5 / 3.5 / 5.5 mm outside pockets; local flanges 3.6 mm / open U access |
| Mid-span Y=−35 area | 69.9 mm² | 277.5 mm² |
| Mid-span Ixx / Izz | 567 / 10289 mm⁴ | 6744 / 23394 mm⁴ |
| Matched gripping tip stiffness, ideal beam | 20.8 N/mm | 181.1 N/mm |
| Estimated gripping deflection at 25 N | 1.2043 mm | 0.1381 mm |
| Estimated lateral deflection at 10 N, coupled sections | 0.0422 mm | 0.0191 mm |
| Lateral deflection with independent-face assumption | 3.5728 mm | 0.1069 mm |
| Root-region maximum nominal bending stress at 25 N | 7.45 MPa | 1.30 MPa |
| Transition / opening corner radii | Sharp large windows | R2.5 outer transitions, R2 core, R3 service window |
| Torsion / warping | Separate open rails | Closed mid-span cell; root service and sensor windows remain open |
| Print orientation and supports | X=−14 side down; exposed large spans | Same orientation; core bridges / pad supports require slicing (NOT VERIFIED) |

Geometry-only beam comparison: **8.72× gripping stiffness**, **2.21× coupled-section lateral stiffness**, with **154.8%** more solid-material mass. These are estimates under matched assumptions, not measured performance. They do not predict stiffness or filament use for the user's **4–5 walls / 25–35% infill** evaluation baseline. The lateral independent-face result shows sensitivity to cross-section coupling; the open baseline is particularly sensitive. No whole-finger torsional stiffness multiplier is claimed.

Calculations use actual CAD slices every 0.5 mm, including bores/windows, with 1 mm convergence and section-area/solid-volume checks. The [JSON](mechanical-comparison.json) records all assumptions and checks; [CSV](section-properties.csv) contains the section properties. Loads act at distal Y=0, with an ideal clamp at Y=−70. The 25 N normal and 10 N lateral loads are representative sensor measurement-range values from the supplied manual, not allowable grip forces. Shear deformation, bolted-joint motion and sensor-housing flexibility are excluded. [Beam method](https://ocw.mit.edu/courses/16-01-unified-engineering-i-ii-iii-iv-fall-2005-spring-2006/f66f80cd5fbd5cf8295d7b1e1e28a368_gm5_8_notes.pdf).

Material reference: **E=1810 MPa** along printed XY and **density 1.28 g/cm³**, from [Bambu PETG HF TDS V1.0](https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf). The user's actual PETG grade and printed properties are unknown. The reference used 100% infill and annealed test specimens; do not assume this part reproduces them. At an assumed half modulus (905 MPa), gripping deflections double to **2.4086 / 0.2761 mm**. This is a sensitivity case, not a validated lower stiffness limit. Mass excludes supports, hardware and real print voids; no slicer or weighing result is implied.

Side printing keeps longitudinal Y fibres and gripping-plane Y–Z load paths within layers. Lateral and torsional loading still impose interlayer shear and splitting risks. Rounded transitions remove sharp geometric notches, but local stress concentration, creep and fatigue life remain unverified. The unchanged root bolt pattern still carries the 1750 N·mm representative root moment; a simplistic bolt-only elastic split gives about 109 N axial load per tension-row screw. Real preload, contact load sharing, thread engagement and polymer bearing must be checked; no torque or safety factor is assigned.

See [manufacturing and assembly notes](manufacturing.md), [actual CAD sections](../drawings/structural_sections.png) and [same-scale CAD comparison](../drawings/v2_structural_comparison.png). Existing PRINT-HOLD remains in force.
