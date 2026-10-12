# Piper dual M2324 tactile sensor adapter

Reversible two-piece clamps for two PaXini **PX6AX-GEN3-IP-M2324-Core / PXSR-STDIP03A** sensors on unmodified AgileX Piper fingers. Each finger uses four M3 clamp bolts and six M1.6 sensor screws, with sensing faces opposed. No drilling, replacement finger or adhesive primary joint.

**Physical fit hold:** only print the fastener coupon and the two fit-gauge pieces. Full adapter STEP/STLs and GLB are digital review artifacts, not a release for printing or operation. Read [PRINT-HOLD.md](PRINT-HOLD.md).

`m2324-reference` preserves the original geometry and exports. `m2324-v2` retains the finger cavity, sensor rear plane, six-hole pattern and assembly transforms, with shallower, fully open M3 head pockets and an external lug print ramp. See [parameter differences](docs/m2324-v2-changes.md), [validation](docs/validation-report.md) and [printing guide](docs/assembly-guide.md).

## Reproduction

Python 3.12.3, environment at `~/workspace/envs/venv/gripper-cad/`. All 59 entries in requirements.lock match. If recreating on another machine, check for an existing suitable environment first:

```bash
uv venv --python python3.12 ~/workspace/envs/venv/gripper-cad
uv pip install --python ~/workspace/envs/venv/gripper-cad/bin/python --cache-dir ~/workspace/.cache/uv -r requirements.lock
source ~/workspace/envs/venv/gripper-cad/bin/activate
python scripts/cad/build_adapter.py --profile m2324-v2
python scripts/cad/build_fit_gauge.py --profile m2324-v2
python scripts/cad/build_assembly.py --profile m2324-v2 --opening-mm 50
python scripts/cad/validate_adapter.py --profile m2324-v2 --report ~/workspace/runs/gripper-tac-cad/2026-10-11_m2324-v2/v2-validation.json
```

The baseline was reproduced separately under `~/workspace/runs/gripper-tac-cad/2026-10-11_m2324-v2/baseline/` from commit `0d7ee279b727843aca92141fbcb6ef7a688d2cf2`; four command logs are in the parent directory. Original project exports were not overwritten. Always specify `--profile m2324-v2` for v2.

Legacy `piper_m2324-reference_assembly*` previews show the older one-sensor study. Use `piper_dual_m2324-v2_*` for the current paired assembly.

STEP/CAD use mm. STL is unitless: import at **1 unit = 1 mm**, without scaling. GLB uses metres. Fit-gauge `_print.stl` files already have the recommended bed orientation; other STEP/STLs retain jaw-local coordinates. The coupon is already on Z=0.

Editable models: cad/source; deliverables: cad/exported; images: drawings/screenshots; original supplier assets: assets/vendor_files; physical forms: measurements. Large logs/intermediates belong under workspace runs/gripper-tac-cad.

The provisional software trial floor is **30 mm commanded opening**, not a final limit or permission to operate. Full closure conflicts with the sensors. Cable plugs, IN/OUT selection, service loops, liners, fastener fit and strength remain unverified. The sensor's 25 N measurement range is not a clamp rating. Resume only after the requested physical data arrive.
