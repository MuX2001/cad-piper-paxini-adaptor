# Design notes

2026-10-11: Selected a two-piece bolted clamshell over the Piper finger's distal section after comparing it with a friction sleeve and an unverified stock-feature bracket. The split clamp captures the tapered finger, uses a printed distal cap against sliding, and has an inner plate for the supplied M2324 mounting pattern. Four external M3 bolts avoid drilling the stock finger. A removable compliant liner is expected to remove play without marking the original surface. See [design-rationale.md](design-rationale.md).

2026-10-11: The user confirmed two M2324 sensors facing each other. Both stock finger meshes use the same local geometry, so each jaw receives one copy of the same inner plate and outer roof. The paired assembly uses each jaw's URDF transform; the active normals oppose in the grasp gap. Each cable passes through its proximal plate window to its outer-roof tie lug. Each sensor reaches 11.403 mm inward, for about 22.806 mm total paired reach. Use a provisional 25 mm minimum commanded opening until physical fit confirms clearance.

Open design decisions: confirm both physical finger dimensions and coatings, screw head geometry, liner thickness, both cable plugs and bend radii, gripping force, and the permissible command floor. No load test, print test, or physical assembly has been performed.
