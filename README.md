# Piper tactile sensor finger adapter

This project develops reversible, FDM-printable clamps for mounting **two PaXini IP-M2324-Core tactile sensors**, one on each **unmodified AgileX Piper gripper finger**, with their active faces facing each other. The stock gripper and sensor CAD files under `assets/vendor_files/` are preserved unchanged. The editable model is build123d Python source in `cad/source/`.

## Current prototype

The user confirmed two **M2324** sensors. The source STEP and manual identify **IP-M2324-Core PXSR-STDIP03A**; `m2324-reference` remains the build profile name because dimensions come from supplied CAD, not physical measurement. See [interface-spec.md](docs/interface-spec.md) and [validation-report.md](docs/validation-report.md).

Each finger receives the same two-piece bolted clamshell. A printed inner plate fastens to each M2324's six mounting holes; an outer roof captures the finger, provides a distal stop, and has an external cable-tie lug. Print **two copies of each part**. No drilling, machining, or finger replacement is required.

## Organizing files

Keep original supplier files in `assets/vendor_files/` or `assets/datasheets/` and record their origins and transformations in [references.md](docs/references.md). Use `cad/source/` for authored CAD, `cad/exported/` for STEP, STL, and GLB deliverables, `drawings/screenshots/` for preview images, `measurements/` for physical dimensions, and `experiments/fit_tests/` for test procedures. Write generated experiment results under `~/workspace/runs/gripper-tac-cad/`.

## Rebuild and inspect

The environment is `~/workspace/envs/venv/gripper-cad/`. If absent, create it outside the repository with `python3 -m venv ~/workspace/envs/venv/gripper-cad`. From this project directory:

```bash
source ~/workspace/envs/venv/gripper-cad/bin/activate
python -m pip install -r requirements.lock
python scripts/cad/build_adapter.py --profile m2324-reference
python scripts/cad/build_fit_gauge.py
python scripts/cad/build_assembly.py --opening-mm 50
python scripts/cad/validate_adapter.py
```

`requirements.txt` lists the direct dependencies; `requirements.lock` records the exact Python 3.12 environment validated on this Ubuntu workstation. The build writes two manufactured STEP solids and two printable STL meshes, each needed twice. The fit-gauge command writes two short test STLs. The assembly command writes an interactive GLB and inspection PNGs with both sensors. STEP carries millimetre units; STL is unitless, so import at **1 unit = 1 mm**. The GLB uses metres by glTF convention. FreeCAD or another STEP-capable CAD program can inspect the neutral solids; no FreeCAD compatibility test has been run.

For visualization, use the `piper_dual_m2324_*` GLB and PNG files. The older `piper_m2324-reference_assembly*` previews show the superseded one-sensor study and are retained as a reference.

The [assembly guide](docs/assembly-guide.md) gives hardware, print orientation, and installation steps. **Use a provisional minimum command of 25 mm opening with both sensors installed:** the paired sensor envelopes overlap near full closure. No physical fit or strength test has been performed.
