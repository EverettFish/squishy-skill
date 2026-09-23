# Slow rising, without a dashboard

The user should understand the page by touching the toy. Keep the default interface pure white and quiet; the model is the point.

## What the included model actually does

`FoamMode` integrates two relaxation states analytically each frame. Their combination gives a quick elastic response plus slower creep and delayed recovery. Constant load deepens the dent; its foam-memory component decays monotonically after release. `JellyMode` adds an exactly integrated underdamped elastic-skin response (natural frequency 13 rad/s, damping ratio .24). Release gives it a bounded impulse, producing a brief positive/negative wobble before settling; it does not replace the slow foam memory. A common-coordinate contact field displaces vertices in the surface normal direction with modest rim bulging and depth attenuation. Global compression reduces height and increases lateral dimensions while allowing air-volume loss. A floor clamp prevents vertices passing through the display floor.

This is a reduced-order viscoelastic approximation intended for interaction, not FEM, a calibrated standard-linear-solid material fit, actual hand collision, or a stress/strain measurement tool. Do not label a progress value as physical pressure. The default UI intentionally hides numerical recovery percentages and simulation jargon.

`recovery` is an approximate settling-time control (2–12 seconds), not an exact stopwatch to 100%. Return is asymptotic until a small rest threshold. Local dents persist after release, up to eight concurrent contact memories. Fine pen pressure is used when available; mouse/touch drag distance changes load. There is no claim of true multi-hand volumetric contact.

## Invariants worth preserving

- Keep all geometry, decorative layers, and hit locations in a shared coordinate system after GLB import.
- Map the selected deformed triangle back to rest-space using barycentric coordinates. Don't place a new contact using already-deformed coordinates.
- Update normals as the object deforms; keep raycast bounds valid as the silhouette expands.
- Integrate using elapsed time, cap giant frame gaps, release loads on pointer cancellation, lost capture, window blur or page hiding.
- Hold-to-squeeze must release on key-up. Don't steal arrow/space input while a range input is focused.
- Orbit interaction should be an explicit toggle, with an easy way back to squeezing.
- Model loading and WebGL failure should leave a readable recovery message and disabled controls, not an empty successful-looking stage.

## QA

Check short vs long press, recovery at 2/6/12 seconds, repeated presses at different places, global squeeze, front/side/back rotation, reset, both sliders, keyboard press/release, and phone layout. On phones the toy should fit above the controls and copy. Resize the camera to fit the viewport, not just the canvas. Respect reduced motion by avoiding unsolicited auto-rotation/demo; user-triggered squishing still works.

The optional `document.modelContext` tools expose readback and recovery adjustment only. Feature-detect support; keep unsupported environments working. Don't claim WebMCP verification if the current host cannot exercise it.
