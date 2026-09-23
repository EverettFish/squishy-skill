# TATA: preserve the reference, then make it soft

The source is already a finished 3D character. Preserve its face, gesture, blue cap/hoodie, TATALAB lettering and original body proportions instead of shortening it into a generic chibi doll.

The front texture is projected onto a closed mesh with inferred rounded depth. Front and back projections blend into a baked atlas; the generated turnaround guides hidden views. The front preserves the source appearance. Side/back anatomy and texture registration are approximations, and extreme side views still show projection stretching. This is not a photogrammetric scan or fully relightable PBR reconstruction. The viewer defaults to the matching front camera, with rotation available for inspection.

`web/likeness.html` compares the original against the actual Blender front render. `renders/` contains front, side, back and three-quarter checks, rendered from geometry rather than substituted reference images.

## Rebuild

Executed with Blender 4.5.9. The supplied mesh data allows rebuilding with Blender's bundled NumPy:

```sh
blender --background --python examples/tata/blender/build_tata_reference.py
blender --background examples/tata/blender/toy.blend --python examples/tata/blender/render_reference_checks.py
```

To regenerate geometry after changing the source, install NumPy, SciPy and Pillow in a project environment and run `blender/prepare_reference_mesh.py` first. It reads source pixels for silhouette/UV registration without editing the source bitmap. Its landmarks are TATA-specific, not a universal automatic converter.

The .blend packs textures, camera, lighting and a 240-frame local press/release/pull/release animation. GIF/MP4 previews sample every second frame at 12 fps. The browser runs live contact dynamics; the timeline is an editable demonstration, not a Blender soft-body cache.

The original image contains baked shading. A texture-led emissive material with a small physical coat preserves its colours. Shape deformation carries all texture details along with the surface.

Character and mark rights remain with their owners. See ASSETS.md.
