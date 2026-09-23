# Local press, outward pull, soft return

The page is white and quiet. Explain implementation here, not beside the toy.

## What ships

`GelContact` maintains a 3D target, elastic position/velocity and slow memory per grab. An exactly integrated damped oscillator follows held targets (frequency 24 rad/s, damping .68); after release, 12 rad/s and .19 damping produce visible overshoot. The elastic contribution is .82 of the target, with .18 slow memory. Memory loads over .5 seconds and relaxes with time constant `recovery/3.4`. These are authored perceptual parameters, not measured material constants. Recovery is approximate, with a small rest threshold.

`contactKernel` caches compact weights `max(0, 1-distance²/radius²)³`. Outside the radius, vertices are exactly unaffected. Press moves inward and bulges the surrounding tangent directions. Pull follows a screen-parallel grab plane plus an outward normal component. `applyGel` always adds the field to immutable rest vertices across all meshes. There is no global scale in this interaction. Target length is limited to 2.25 normalized units; floor contact is clamped. Up to five recent grab memories coexist.

The browser normalizes toys to about four scene units. Default radius is about 1.3 units and press depth .7, deepening during a downward drag. Tune the radius with model scale. A cheek press must leave distant feet still.

This is a reduced-order viscoelastic interaction, not FEM, volume-conserving fluid simulation, self-collision, tearing or exact hand contact. Extreme pulls may fold surfaces or intersect nearby parts. Do not claim perfect physical accuracy. Legacy `FoamMode` / `JellyMode` exports remain for compatibility and the historical foam animation.

## Invariants

- Bake meshes and hit positions into common coordinates after GLB import.
- Map a hit on a deformed triangle back to rest space with barycentric weights.
- Eyes, mouths, lettering and accessories follow the same field as their supporting surface.
- Update normals and raycast bounds as shape changes.
- Integrate elapsed time, bound large gaps and release on pointer cancellation, lost capture, blur or hiding.
- Space holds a local press, key-up releases; do not steal input from sliders/text.
- Press / Pull / Rotate are explicit modes. Shift-drag is an optional pull shortcut. Disable orbit while grabbing.
- Loading and WebGL errors show a readable message rather than an empty success-looking stage.
- No autoplay spin/demo. Respect reduced-motion preferences for decorative transitions.

## QA

Test a visibly deep press and outward mouse drag, short/long holds, release overshoot/settling, overlapping contact memories, rotation/reset, sliders, keyboard release and phone fit. Compare remote points before/after local press. Inspect a deformed frame, not merely the status text. Run `node --test tests/physics.test.mjs tests/gel.test.mjs` after shared physics changes.

Optional WebMCP tools expose readback and the visible recovery setting. Feature-detect them; normal play does not require WebMCP.