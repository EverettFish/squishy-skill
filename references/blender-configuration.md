# Blender settings that travel with the toy

Use Blender 4.5 LTS or newer. Example builds were executed with 4.5.9. Run Blender's bundled `bpy`; don't install `bpy` into the host Python as a substitute.

## Find once, run explicitly

```sh
python scripts/ensure_blender.py --search-root /path/to/workspace
# Only if absent:
python scripts/ensure_blender.py --install
"/absolute/path/to/blender" --background --python /absolute/path/to/build.py
```

PowerShell needs the call operator before a quoted executable path:

```powershell
& 'D:\tools\blender\blender.exe' --background --python 'D:\my-toy\blender\build.py'
```

Quote absolute paths, including Chinese/spaces. Resolve output folders relative to `__file__`, not the working directory; create parents first. Keep tools, logs and temporary renders out of distributable skills. Reuse a discovered installation. The installer checks official SHA-256 manifests and installs into a user cache, without changing global PATH.

## Geometry conventions

- Author with **+Z up, front toward -Y**, around 3–4 units tall. `export_yup=True` maps to browser +Y up, front +Z.
- Apply location, rotation and scale before common-space shape keys. Update the view layer before reading world matrices or building BVH projectors.
- Round heads often need depth around 80–100% of width. Derive actual dimensions from the turnaround. Short broad torsos and small limbs help the mochi silhouette.
- Start spheres at 48 × 32; hero heads at 64 × 48. For connected same-material volumes try voxel size .035–.05, smoothing 4–6 iterations, then one subdivision. Don't union all colours and lose material boundaries.
- Hide joins between differently coloured volumes inside the surface. Give cap bills and thin accessories real thickness. Inspect fingers, cuffs and ears for gaps.
- Project markings onto the finished core with BVH rays; offset about .01–.025. Give patches enough subdivisions to deform. Transform and triangulate text, subdivide its faces and project onto clothing. Coarse voxel remeshing damages small letters.
- Aim for roughly 40k–120k total vertices for desktop examples, then profile on phones. Avoid adding heavy subdivision to every eye layer.

## Material presets

Use Principled BSDF named inputs in 4.5. Helpers provide `foam_material` and `gel_material`.

| Setting | Foam | Gel / silicone |
|---|---:|---:|
| Roughness | .75–.85 | .28–.38 |
| Subsurface Weight | .10–.15 | .10–.18 |
| Subsurface Radius | (1, .5, .25) | (1, .45, .22) |
| Coat Weight | 0–.08 | .3–.5 |
| Coat Roughness | .3 | .22–.3 |
| Metallic | 0 | 0 |

Foam may use Noise → Bump (scale 155, strength .18, distance .01). Gel needs smooth broad highlights. Transmission is optional for translucent subjects; don't expose intersecting internal meshes by making opaque characters transparent. GLB doesn't preserve all procedural shaders: the viewer recreates a physical material using exported colours/maps. Check Blender and browser separately.

## Studio and fast iteration

`studio_scene(target, ortho_scale, preview=True)` creates a camera, three area lights and white world. Add the floor separately; don't export studio objects as the toy.

- Final still: Cycles, 32–64 samples, denoising, around 900 × 1000, AgX.
- Fast animation: `BLENDER_EEVEE_NEXT`, `scene.eevee.taa_render_samples=16`, around 520 × 560. If rendering every second frame from a 24 fps timeline, encode at 12 fps to preserve speed.
- Inspect orthographic front/side/back and three-quarter renders, then the actual browser perspective.
- GPU is optional. Fall back to CPU/EEVEE when unavailable; don't assume CUDA/OptiX. Check exit codes and output files before reporting success.

## Editable local motion

Create Rest, three local displacement shape keys and an optional tangential bulge key. For rest vertex `x`, centre `c`, radius `r`, use `w = max(0, 1 - |x-c|²/r²)³`. Outside support, displacement is zero. Use identical fields across all meshes, including facial paint and letters.

Sample the elastic oscillator and slow memory from the web interaction at 24 fps. Animate key values and mark press, release, pull, release. `examples/tata/blender/build_tata_reference.py` is an executed example. These keys demonstrate local dynamics; they are not a baked Blender soft-body solver.

## Reliable GLB export

1. Set the unpressed rest frame and zero deformation keys.
2. Deselect all, then select toy meshes only. Exclude floor, lights, camera, reference planes and helpers.
3. Export with `use_selection=True`, `export_yup=True`, `export_animations=False`, `export_morph=False`. Live browser deformation must not be doubled by baked animation.
4. Save `.blend` with the studio and playable timeline. Include the construction script and chosen generated reference.
5. Serve over HTTP; `file://` cannot reliably load modules/GLB. Verify the model, local dent, outward pull and attached details.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Flat side | Rebuild volume from the side reference; changing camera won't fix it. |
| Hair through cap | Recess fringe and add cap thickness; check multiple views. |
| Rigid eyes/letters | Apply the shared rest-space field to every mesh. |
| Paint intersects | Reproject onto the final core with a small offset. |
| Metallic look | Metallic zero, softer environment, higher roughness. |
| Whole toy shrinks | Remove global scale from local interaction. |
| Slow frame rate | Reduce detail layers, cache contact kernels, profile normal updates. |
