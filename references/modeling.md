# Modeling a soft, complete object

Use Blender 4.5+ and Python for reproducible construction. Run background jobs with a saved log; inspect the exported model/render before delivery. Blender uses +Z up, front -Y; export glTF as +Y up. The viewer normalises the GLB to its display bounds and deforms all parts in the same world space.

## Shape

Match the selected sheet before adding small details. Use rounded primitives, curves, profile lofts, sculpting or another method suited to the subject. A loaf, animal, sneaker and flower should not share one prescribed construction. Parameterise major proportions so changes don't require rebuilding all feature coordinates.

For compound foam bodies, apply primitive transforms, join the core volumes, voxel-remesh at roughly 1–2% of the object's height, smooth the union, and use limited subdivision. Inspect junctions around limbs and ears. Target about 30–100k render vertices total for comfortable browser interaction; measure rather than blindly adding subdivision. Separate decorations can remain separate meshes if their positions lie on the core and they use the common deformation field.

Use ray projection/BVH to conform belly patches, cheeks and mouth to the curved surface. Do not approximate a curved face with a rectangle at fixed depth: it will slice into the head or float. When using layered eye patches, offsets need only be a small fraction of model size. Rays must hit the intended body part, particularly with folded limbs or overlapping accessories.

## Materials

For Blender's foam, start around roughness .75–.9, restrained subsurface weight .08–.16, gentle sheen, noise-driven microscopic bump. Adjust for the subject. Do not mistake roughness for a grainy silhouette. Eye paint may be a little glossier, but must still deform. Keep bright colours readable under neutral high-key lighting.

The viewer transfers GLB material colours, roughness and texture maps, then adds restrained procedural bump to materials named `Foam`, `Mango`, `Vanilla`, `Peach` or listed with a foam-like name. Avoid depending on Blender procedural nodes to automatically survive GLB export; bake important maps or recreate the intended surface in the viewer.

## Editable motion

Include a playable Blender squeeze/release preview with the same soft Q-elastic wobble followed by slower recovery. Sample the slow memory and damped skin modes into separate shape-key tracks so the user can adjust the softness and jiggle independently. Keep overshoot restrained and the base in contact with the floor. Clearly describe it as a sampled deformation preview; do not call keyframed shape keys a Blender soft-body solver. Browser interaction comes from the shipped dynamic constitutive model. Both must show consistent softness and a plausible return to rest.

## Final inspection

Compare front identity, side thickness, back completion and three-quarter readability with the reference. Check that the mouth is truly attached, markings stay aligned under a squeeze, and nothing tears or jumps. The floor is a contact plane, not a cutout hiding the model's bottom. Use soft contact shadow and neutral surroundings.
