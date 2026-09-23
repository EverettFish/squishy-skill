# 奶龙，下班之后 / Nailong, off duty

先生成 `turnaround.png`，再根据正、侧、背三视图重建。团子版头部宽 2.56、深 2.26、高 2.32，总高约 3.44；身体宽 2.2、深 1.92，四肢缩短。表情和肚皮贴合曲面，随身体一起变形。使用 `turnaround-round-prompt.txt` 生成最终参考。

The turnaround came first. The mochi head is 2.56 units wide, 2.26 deep and 2.32 tall, at a total height of about 3.44. The body is 2.2 wide and 1.92 deep, with tiny limbs and a tail extending behind it. Facial details and the belly patch follow the curved surface and deform with the body. The final reference uses `turnaround-round-prompt.txt`.

Open `toy.blend` to edit. Its timeline includes separate slow-rise and Q-elastic-jiggle shape-key tracks, with press/release markers. `build.py` reconstructs the Blender project and GLB using Blender 4.5+:

```sh
blender --background --python examples/nailong/build.py
python scripts/serve.py examples/nailong/web
```

Browser controls: hold the toy for a local dent, hold the yellow button or Space for a whole-body squeeze, and toggle rotation to look around. Feel settings stay tucked away.

The webpage runs an interactive viscoelastic approximation; Blender's preview is keyframed deformation, not a baked soft-body solver. Neither is a material calibration or production-ready physical toy specification. Character rights are described in `../../ASSETS.md`.
