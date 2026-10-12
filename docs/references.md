# Source references and asset integrity

All supplier files below are preserved unchanged under `assets/vendor_files/`. The AgileX URDF package identifies its license as MIT; the supplied PaXini file license is not stated in the local package. Do not edit either source in place.

| Source | Use and unit | SHA-256 |
| --- | --- | --- |
| `agx_arm_urdf-main/piper/urdf/piper_with_gripper_description.xacro` | Piper frames, jaw axis and limits; metres | `374013965d83e80923196598c0bfbba2b0703b9f412ed9ec255c82b5c50e0f53` |
| `agx_arm_urdf-main/agx_gripper/meshes/gripper_link1.stl` | Original finger envelope; coordinate values in metres | `475a7d8db056524d7659fadf5a2c307d62791047b6214d733dfc7846ed1c613d` |
| `GEN3触觉传感器3D模型/3D Models 3D图纸/Finger pad 指腹 M2324 PX6AX-GEN3-IP-M2324-Core PXSR-STDIP03A.stp` | M2324 shape and six mounting axes; STEP declares millimetres | `8d57e826d53e185d4657f89595abdb29eb8e7cc2fdd572a87bfa5956ae1b7707` |
| `f8aeeeec-332a-4f38-a9f9-f5c3f4a8c83d.pdf` | PaXini sensor manual; M2324 dimension drawing PDF p. 8, handling caution PDF p. 20 | `2901a1f76e65287d47c46cb23216b912656de1f841188a3f41ef127984c4395b` |

The vendor STEP was **imported read-only**, rotated 180° about its X axis, then translated by (0, −0.8, −5.35) mm in each jaw-local frame for the virtual two-sensor assembly. Vendor STL coordinates were multiplied by 1000 to convert metres to millimetres for CAD checks; the GLB visualization converts the whole assembly back to metres. The STEP and mesh originals were not rewritten.

Manufacturer model naming is also listed on [PaXini's GEN3 product page](https://www.paxini.com/news/ax/gen3), which identifies `PX6AX-GEN3-IP-M2324-Core`. PETG selection for a first printed clamp is supported as a general material use by [Prusa's PETG guide](https://help.prusa3d.com/article/petg_2059); no material strength test on this adapter has been done.

## V2 provenance and conversions

The AgileX package was supplied locally as `agx_arm_urdf-main`; upstream source URL and exact upstream revision were not captured and remain unknown (do not infer them from the folder name). License: package-declared MIT; native URDF/STL/DAE coordinates: metres. The locally supplied PaXini STEP/manual version and original download URLs are unknown; product family is PX6AX-GEN3-IP-M2324-Core / PXSR-STDIP03A. The product-page link above is contextual, not a verified download URL. STEP/dimension drawings use millimetres; PaXini asset license is unspecified. SHA-256 values above identify the exact supplied files.

V2 applies the same read-only imports, metre↔millimetre conversions and sensor/jaw transforms. No vendor modifications or mesh repairs were performed. The authored v2 changes are listed in m2324-v2-changes.md. Print-gauge copies translate inner Z by +3.2 mm; roof copies rotate −90° about X then translate Z by +2.1 mm. These proper rigid transforms put bases at Z=0 without scaling. Review sections are 0.1 mm CAD slices at Y=−6…−5.9. GLB remains in metres; exported manufacturing STEP/STL remain in mm. Machine validation evidence hashes all supplied files and CAD source/scripts. Legacy exports are retained unchanged.
