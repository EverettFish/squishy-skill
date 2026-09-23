import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));s=bpy.context.scene;cam=s.camera
s.render.resolution_x=600;s.render.resolution_y=800;s.eevee.taa_render_samples=32
s.use_nodes=True;nodes=s.node_tree.nodes;nodes.clear();layer=nodes.new('CompositorNodeRLayers');bg=nodes.new('CompositorNodeAlphaOver');bg.inputs[1].default_value=(1,1,1,1);out=nodes.new('CompositorNodeComposite');s.node_tree.links.new(layer.outputs['Image'],bg.inputs[2]);s.node_tree.links.new(bg.outputs['Image'],out.inputs[0])
for label,loc in [('front',(0,-12,2.05)),('side',(12,0,2.05)),('back',(0,12,2.05)),('three-quarter',(5,-12,2.05))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,2.05))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=os.path.join(ROOT,'renders',label+'.png');bpy.ops.render.render(write_still=True)
cam.location=(0,-12,2.05);cam.rotation_euler=(Vector((0,0,2.05))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=480;s.render.resolution_y=640;s.eevee.taa_render_samples=16;s.frame_start=1;s.frame_end=239;s.frame_step=2;s.render.filepath=os.path.join(ROOT,'renders','reference-motion','frame-');os.makedirs(os.path.dirname(s.render.filepath),exist_ok=True);bpy.ops.render.render(animation=True)
