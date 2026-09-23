# Same character first. Soft toy second.

Never replace a supplied character with a generic cute doll and call that a faithful model. Roundness is an art-direction option, not permission to lose identity.

## Choose the right path

- **Finished 3D reference / exact-match request:** preserve face, head-to-body ratio, pose, accessories, colour and typography. Use the original as the front appearance authority. Generate consistent missing views rather than redesigning the front. Build geometry to its silhouette and landmarks; use source-projected textures, proper UV painting or existing textured 3D assets when available.
- **Photo or drawing to a new cute style:** generate an agreed style reference first, but preserve recognisable features. Round the volume without substituting a stock face.
- **Food / object:** follow its own silhouette and material; don't invent facial features or mascot proportions.

No image tool or automatic image-to-3D service is guaranteed. Discover real available tools. If none produces a faithful asset, use explicit Blender geometry and texture projection. Do not claim hidden-angle accuracy from a single view.

## Reference-projected volume

For already-rendered front-facing characters, map the original image onto actual front geometry using an orthographic camera and projective UVs. Keep X/Z landmark registration, infer meaningful depth from head/body/limb profiles and a consistent side reference, and provide a closed rear surface. Build cap bills, noses, hair and accessories where they materially affect profile. A flat card, front-only relief or camera trick does not satisfy full 3D reconstruction.

Use dedicated back/side maps or bake a coherent atlas. Inspect seams and avoid projecting white background pixels onto edges. Pack the images into `.blend` and GLB, preserve texture colour space, and include a reproducible source/texture manifest. Do not publish private source material without authorization.

Baked reference images already contain shading. Double lighting can bleach faces and turn cloth into shiny plastic. In the browser, `referenceTexture: true` uses a texture-led emissive base with a small physical coat; ordinary unbaked models keep the normal material path. This prioritizes source appearance over fully relightable PBR. Texture highlights/shadows remain partially baked; don't claim they are physically dynamic. For a fully relightable asset, use properly de-lit albedo/normal/roughness maps.

Preserve UVs throughout local deformation. Every visible detail must stretch with the underlying mesh. Keep generated geometry genuinely volumetric, but distinguish inferred geometry from reconstructed evidence in project notes.

## Mandatory likeness gate

1. Render the unpressed model from a camera matching the original. Normalize subject height and place reference and render side by side.
2. Compare silhouette, head width/height, face outline, eye spacing and shape, brow/hairline, nose, mouth/expression, hat brim, body/limb proportions, gesture, clothing edges, colours and exact text.
3. If the source is already 3D, use the actual source pixels for high-value details where possible. Do not replace a recognizable face with ellipsoids and disk eyes to save modeling work.
4. Inspect side, back and three-quarter views for false flatness, stretched faces, duplicated features, texture seams, white fringes and intersections. Fix what is visible; disclose remaining inferred-view limitations.
5. Inspect the loaded browser version too. A good Blender render does not prove the exported materials, UVs or camera are correct.

Do not report success merely because a model is round or technically loads. If it is a different-looking character, revise it before delivery. Never promise pixel-identical unseen angles without the reference data needed to support that claim.
