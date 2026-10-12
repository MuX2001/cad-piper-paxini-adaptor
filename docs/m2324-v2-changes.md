# M2324 reference → v2 differences

Baseline: `0d7ee279b727843aca92141fbcb6ef7a688d2cf2`. Profile selection is in `cad/source/parameters.py`; all lengths below are mm. Geometry changes are confined to M3 pocket mouths/seats and external roof material.

| Parameter or constraint | m2324-reference | m2324-v2 | Reason / status |
| --- | --- | --- | --- |
| `roof_wall` | 3.0 | 3.0 | Preserve roof datum |
| `bolt_head_recess` | 2.2 | 0.5 | Raise seat 1.7; head protrudes |
| `open_head_pockets` | false | true | Cut through sloped exterior; remove pocket-mouth skin |
| `lug_print_ramp_run` | 0 | 8.0 | External lead-in for distal-end-down printing |
| `m16_diameter_compensation` | 0 | 0 | Added diametral offset; physical data pending |
| `m3_diameter_compensation` | 0 | 0 | Same |
| `head_diameter_compensation` | 0 | 0 | Both M1.6/M3 head diameters; same |
| `nut_across_flats_compensation` | 0 | 0 | Across-flats offset, not radial; same |
| Nominal M1.6 / M3 bore | 1.8 / 3.4 | unchanged | Nominal clearance is not universal print compensation |
| Nominal M1.6 / M3 head hole | 3.2 / 6.2 | unchanged | Actual hardware unmeasured |
| Nut circumradius / depth | 3.3 / 2.6 | unchanged | Across flats = 5.716; fit pending |
| Finger cavity / split | original | unchanged | Same taper, roof, bottom −0.6, split Z=4, distal stop |
| Sensor interface | six axes; rear plane Z=−3.2 | unchanged | Inner plate geometrically identical |
| Sensor model / pose | M2324, Rx180°, (0,−0.8,−5.35) | unchanged | Two active faces oppose |
| Window / tie hole | 10.5×12 / Ø3.2 | unchanged | Cable envelope unverified |
| Roof printing | split face on bed | distal Y=2.1 face on bed | Avoid cavity bridge without changing datums |
| Provisional software floor | 25 | 30 | Trial setting, not final clearance |

The 3.0−2.2=0.8 roof-wall subtraction was a conservative warning, not actual axial support under the side-mounted M3 seats: these lie outside the cavity over solid side walls. V2 raises the seats and checks at least 2 mm of material beneath their annuli. Allowing for exterior slope across a 3.1 mm head radius gives **3.0−0.5−(3.6/27.6)×3.1 = 2.096 mm**. Actual seat-to-split distances are 9.287 mm proximal and 7.461 mm distal. These are geometry checks, not strength ratings.

## Recalculated screw reach

Nut top is at the pocket ceiling Z=−0.6; no washer modeled. Reach into the nut region = `under-head screw length − (head seat Z − nut top Z)`. Actual engagement also depends on nut height, lead-in, tip and tolerances.

| Station Y | Seat Z | Seat → nut top | M3×14 reach | M3×16 reach | M3×18 reach |
| --- | ---: | ---: | ---: | ---: | ---: |
| −20 | 13.287 | 13.887 | 0.113 | 2.113 | 4.113 |
| −6 | 11.461 | 12.061 | 1.939 | 3.939 | 5.939 |

Old proximal ×16 / distal ×14 lengths are not validated for v2. For an **illustrative, unverified 2.4 mm nut**, neither traverses its full height. Proximal ×18 / distal ×16 are test candidates only, with about 1.713 / 1.539 mm protrusion below that example nut. Measure real engagement and protrusion before choosing. Do not tighten a screw catching only the thread lead-in. M1.6×3 retains calculated 1.6 mm penetration past the 1.4 mm plate into reference 2 mm tapped depth; actual head fit and bottoming remain unverified.

## Printing and retention

An internal arch would move the existing roof/liner datum or intrude into the protected cavity. V2 instead prints along −Y, starting with the distal wall; the cavity stays open in subsequent layers, avoiding the 23.8–32.4 mm bridge. The external lug lead-in is approximately 42° from print vertical, below 45°. Horizontal M3/head/tie holes still need slicer inspection and possible accessible local supports. This is geometric reasoning, not verified slicing or printing.

The inner plate prints on its sensor-mounting exterior; nut-pocket ceilings span about 5.716 mm across flats and may need support. Fit gauges retain Y=−10…2.1, distal taper, 1.5 mm end wall and both complete distal M3 positions. They do not test the proximal cavity, lug ramp or full-part stiffness.

Rigid cavity clearance is positive. Closing split faces alone does not grip the finger by hard-plastic interference: preload relies on compressed removable liners. No material, hardness or friction coefficient is selected; no locating groove is added. Record upper/lower thicknesses and local total interference `t_top+t_bottom−(top clearance+bottom clearance)`. Positive interference is a compression requirement, not verified force. Top/bottom liners can leave lateral gaps (see validation report); centering and slip require measurement. Adhesive is not the primary load path.
