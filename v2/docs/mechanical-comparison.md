# V2 simplification: measured CAD sections

The root region Y ≤ −56 is unchanged by exact solid comparison (difference 0.000000 mm³). The outside bounds, functional datums and continuous sensor outer rails are unchanged (rail difference 0.000000 mm³). Filling the enclosed arm core leaves a continuous solid middle section; no new ribs or external reinforcement were added.

CAD faces: **226 → 120**. Volume: **22245.1 → 25772.9 mm³**. The existing cable saddle is one concentric circular section instead of a nine-section loft.

| Native Y (mm) | Area ratio | Ixx ratio | Izz ratio |
| ---: | ---: | ---: | ---: |
| -69 | 1.000 | 1.000 | 1.000 |
| -60 | 1.000 | 1.000 | 1.000 |
| -50 | 1.171 | 1.018 | 1.040 |
| -35 | 1.480 | 1.092 | 1.147 |
| -15 | 0.818 | 0.709 | 0.738 |

Ratios are simplified / previous reinforced V2. Root and arm sections preserve or increase these geometric properties. The sensor section deliberately replaces tall pocket-dividing walls with a continuous short seating plate, while retaining the outer rails. These area moments are not printed-part strength predictions. Local clamping, creep and fatigue remain physically unverified.

[Full measurements](mechanical-comparison.json) · [Section CSV](section-properties.csv) · [Preserved previous revision](../revisions/before-geometry-simplification/README.md)
