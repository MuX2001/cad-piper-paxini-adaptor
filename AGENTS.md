# Repository Guidelines

## Purpose and layout

This is a mechanical CAD integration project for a tactile sensor adapter on an AgileX Piper gripper. Keep authoritative build123d Python models in `cad/source/`, generated STEP/STL files in `cad/exported/`, imported meshes in `cad/meshes/`, and external documents and CAD assets in `assets/`. Put inspection code in `scripts/`, measured values in `measurements/`, and design decisions in `docs/`.

## Source and reference integrity

Preserve original CAD and datasheet files. Never overwrite imported vendor files; make a separately named working copy in `cad/source/` when modification is required. Record the supplier, source URL, version, license, native units, and every modification or conversion in `docs/references.md`. Keep exports separate from editable source files and regenerate them from the source when design changes.

## Mechanical design practice

Record assumptions about dimensions, tolerances, materials, fasteners, clearance, and the gripper and sensor mounting interfaces in `docs/interface-spec.md` or `docs/design-notes.md`. Mark unverified dimensions clearly. The user confirmed two M2324 sensors; M3234 is not this design target. Update measured interfaces in `cad/source/parameters.py` only after physical data arrive and the Goal is resumed. Document coordinate origins, axis directions, and units before converting or generating meshes; STL itself carries no unit declaration.

## Scripts and verification

Use the workspace Python environment at `~/workspace/envs/venv/gripper-cad/`; keep dependency declarations with this project. Do not create an environment inside this directory or install packages into system Python. Run `scripts/cad/validate_adapter.py` after changing geometry. Keep the stock finger unmodified, and do not command full gripper closure with the current inner-face sensor prototype. For each fit test, record source CAD revision, settings, units, and measured result. Keep large generated outputs under `~/workspace/runs/gripper-tac-cad/`.

## Changes and review

Make focused changes and preserve uncommitted work. A change to geometry should include the reason, key dimensions or constraints, verification method, and an updated drawing or screenshot when useful. Baseline commit is `0d7ee279b727843aca92141fbcb6ef7a688d2cf2`. Preserve reference exports and keep v2 separate. Follow `PRINT-HOLD.md`: coupon and fit gauges only until physical results are reviewed.
