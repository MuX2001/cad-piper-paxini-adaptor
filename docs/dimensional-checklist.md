# Physical dimensional verification checklist

Measure the actual hardware before printing the full adapter or enabling grasp motion. Record the instrument, uncertainty, date, and result beside each item.

| Check | CAD reference or requirement | Actual measurement / result |
| --- | --- | --- |
| Sensor identities, both units | User confirmed two M2324; supplied assets say IP-M2324-Core | Pending physical label checks |
| Finger width at local Y = −25, −15, and −2 mm, both jaws | STL sections approximately 30.1, 27.2, and 21.3 mm | Pending |
| Finger thickness and surface condition at those stations, both jaws | STL roof approximately 10.8, 8.6, and 7.1 mm above local Z = 0 | Pending |
| Distal-end clearance behind printed cap | Modeled 0.6 mm | Pending |
| Sensor body and mounting face | Supplied M2324 STEP 23.819 × 23.602 × 8.203 mm | Pending |
| Sensor tapped holes | Supplied M2324 STEP: X = ±8.75, Y = 3/11/19 mm; manual: M1.6 × 2 mm deep | Pending |
| Screw head fit and engagement | M1.6 head ≤3.2 mm; target engagement ~1.6 mm | Pending |
| M3 nut traps and bolt protrusion | 6.6 mm circumscribed trap; four side bolts | Pending |
| Cable plugs, service loops, and bend radii, both sides | Central plate window 10.5 × 12 mm; external tie hole Ø3.2 mm | Pending |
| Gripper command floor | Provisional 25 mm; paired CAD envelope gap about 2.2 mm | Pending physical check |
| Both sensor active faces and zero-load readings | Faces oppose; no printed part should press either active surface | Pending |
| Clamp slip and plate deflection under a controlled low-force contact | Must not loosen, rub the sensor housing, or pull the cable | Pending |

Pass the short fit gauge before the full print. If the finger differs materially from the mesh, update `cad/source/parameters.py`, regenerate, and rerun `scripts/cad/validate_adapter.py`.
