# Interface specification — preliminary

All dimensions below are in millimetres unless noted. Values derived from the supplied URDF and meshes are reference geometry, not physical metrology. The original vendor files remain unchanged.

## Piper gripper

Source: `assets/vendor_files/agx_arm_urdf-main/piper/urdf/piper_with_gripper_description.xacro` and `assets/vendor_files/agx_arm_urdf-main/agx_gripper/meshes/`.

- The gripper base is fixed 4.5 mm beyond the Piper flange. The two moving finger links originate 138 mm along the gripper-base Z axis.
- The gripper command is a 0–100 mm prismatic displacement; each jaw moves 0–50 mm from the closed position in opposite directions. The finger mesh used for collision has no mesh-scale tag; its 0.0765 m length is consistent with the URDF's metre coordinates and the DAE's explicit `meter="1"` unit declaration.
- Each finger mesh spans approximately X = ±28 mm, local Y = −76.5…0 mm, and local Z = 0…26.5 mm. At local Y = −2 mm, the cross section spans X = ±10.66 mm and Z = 0…7.06 mm; at Y = −25 mm, X = ±15.06 mm and Z = 1.33…10.78 mm. These sections came from the STL triangles and should be checked on the physical finger before committing to a clamp fit.
- With the gripper closed, the two finger contact planes meet at the gripper-base Y = 0 plane. Two opposed sensors reduce the safe minimum commanded opening by the sum of their inward protrusions.

## Target sensor

The user confirmed **two M2324 sensors facing each other**. The supplied CAD and manual identify **IP-M2324-Core PXSR-STDIP03A**. The same sensor-local transform and printed parts are used on both jaw-local frames; the mirrored URDF placements point the active normals toward +Y and −Y in the gripper-base frame.

The manual's dimension drawing (PDF page 8, printed page 5) shows a 23.82 × 23.60 × 8.20 mm envelope, six M1.6 tapped holes to 2 mm depth, 17.50 mm spacing across the two columns, and 8.00 mm between adjacent rows. STEP import measures 23.819 × 23.602 × 8.203 mm and locates the modeled hole axes at X = ±8.75 mm, Y = 3/11/19 mm on the rear. The raised sensing side is toward native +Z; the virtual assembly rotates it toward the grasp gap on each jaw. The manual states ±0.05 mm positional-hole linear tolerance and ±0.1 mm for other unspecified dimensions. Its handling section (PDF page 20, printed page 17) cautions that loading the housing outside its mounting connection can make resultant-force data inaccurate. The M2324 connection diagram on PDF page 13 identifies a DF53-8S-0.6H eight-pin connector, but the cable plug and bend envelope are not dimensioned in these assets.

The M2324 row in the manual's product table (PDF page 5, printed page 2) lists a 0–25 N normal measurement range and ±10 N tangential range. These describe the sensor, not a validated load rating for the printed adapter.

## Measurements still required

1. Measure both physical fingers' distal widths and thicknesses at the planned clamp stations, including coating or pads.
2. Confirm both sensors' mounting-face orientation, connector envelopes, permissible screw engagement, sensing areas, and allowable contact loads.
3. Check the two cable routes and service loops throughout jaw motion.
4. Confirm the minimum commanded gripper opening with both sensors installed, actual material, fasteners, and printer-specific fit clearance.
