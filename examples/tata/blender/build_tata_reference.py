"""Reference-projected volumetric TATA, with packed textures and local gel keys."""
import bpy,numpy as np,os,math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with np.load(os.path.join(ROOT,'blender','reference-mesh.npz')) as archive:data={key:archive[key] for key in archive.files}
def image_material(name,path):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(0,0,0,1);p.inputs['Roughness'].default_value=.45;p.inputs['Coat Weight'].default_value=.10;p.inputs['Coat Roughness'].default_value=.3
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(path);tex.image.pack();m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1
 return m
front=image_material('Reference front',os.path.join(ROOT,'references','faithful','front.png'))
back=image_material('Inferred back',os.path.join(ROOT,'references','faithful','turnaround.png'))
me=bpy.data.meshes.new('Reference volume');me.from_pydata(data['vertices'],[],data['faces']);me.update();o=bpy.data.objects.new('TATA • reference-projected volume',me);bpy.context.collection.objects.link(o);me.materials.append(front);me.materials.append(back)
uv=me.uv_layers.new(name='Reference projection')
uvf=me.uv_layers.new(name='Front source');uvb=me.uv_layers.new(name='Back source');uvs=me.uv_layers.new(name='Side source')
for poly in me.polygons:
 poly.material_index=int(data['materials'][poly.index]);poly.use_smooth=True;source=data['uvfront'] if poly.material_index==0 else data['uvback']
 for li in poly.loop_indices:
  vi=me.loops[li].vertex_index;uv.data[li].uv=(data['uvfront'][vi][0]*.5+poly.material_index*.5,data['uvfront'][vi][1]);uvf.data[li].uv=data['uvfront'][vi];uvb.data[li].uv=data['uvback'][vi];uvs.data[li].uv=data['uvside'][vi]
bpy.context.view_layer.objects.active=o;o.select_set(True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
# Smooth only silhouette-scale stair steps; retain texture registration.
sm=o.modifiers.new('Smooth sampled contour','SMOOTH');sm.factor=.55;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
me=o.data
# Blend three reference projections across lateral surfaces and bake a single atlas.
# Front-facing facial landmarks keep the original image; inferred views fill the rim/rear.
attr=me.color_attributes.new(name='Projection mix',type='FLOAT_COLOR',domain='POINT')
for vtx in me.vertices:
 fb=max(0,min(1,.5+vtx.co.y/.28));nx=abs(vtx.normal.x);side=max(0,min(1,(nx-.72)/.25));side=0
 attr.data[vtx.index].color=(fb,side,0,1)
m=bpy.data.materials.new('Three-view texture projection');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs['Surface'])
textures=[]
for layer,im in [('Front source',bpy.data.images.get('front.png')),('Back source',bpy.data.images.get('turnaround.png')),('Side source',bpy.data.images.get('turnaround.png'))]:
 u=n.new('ShaderNodeUVMap');u.uv_map=layer;t=n.new('ShaderNodeTexImage');t.image=im;l.new(u.outputs['UV'],t.inputs['Vector']);textures.append(t)
a=n.new('ShaderNodeVertexColor');a.layer_name='Projection mix';sep=n.new('ShaderNodeSeparateColor');l.new(a.outputs['Color'],sep.inputs[0])
mix=n.new('ShaderNodeMixRGB');l.new(sep.outputs['Red'],mix.inputs[0]);l.new(textures[0].outputs['Color'],mix.inputs[1]);l.new(textures[1].outputs['Color'],mix.inputs[2])
mixside=n.new('ShaderNodeMixRGB');l.new(sep.outputs['Green'],mixside.inputs[0]);l.new(mix.outputs[0],mixside.inputs[1]);l.new(textures[2].outputs['Color'],mixside.inputs[2]);l.new(mixside.outputs[0],em.inputs['Color'])
me.materials.clear();me.materials.append(m)
for poly in me.polygons:poly.material_index=0
atlas=bpy.data.images.new('TATA baked projection',width=2048,height=2048,alpha=False);target=n.new('ShaderNodeTexImage');target.image=atlas;n.active=target;me.uv_layers.active=me.uv_layers['Reference projection'];me.uv_layers['Reference projection'].active_render=True
bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.samples=1;bpy.context.scene.render.bake.margin=8;bpy.ops.object.bake(type='EMIT')
os.makedirs(os.path.join(ROOT,'references','faithful'),exist_ok=True);atlas.filepath_raw=os.path.join(ROOT,'references','faithful','atlas.png');atlas.file_format='PNG';atlas.save();atlas.pack()
final=bpy.data.materials.new('Reference texture with soft coat');final.use_nodes=True;p=final.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(0,0,0,1);p.inputs['Roughness'].default_value=.48;p.inputs['Coat Weight'].default_value=.08;p.inputs['Coat Roughness'].default_value=.3;p.inputs['Emission Strength'].default_value=1
t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=atlas;u=final.node_tree.nodes.new('ShaderNodeUVMap');u.uv_map='Reference projection';final.node_tree.links.new(u.outputs[0],t.inputs['Vector']);final.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color']);me.materials.clear();me.materials.append(final)
os.makedirs(os.path.join(ROOT,'web','assets'),exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'web','assets','toy.glb'),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_yup=True)
center=Vector((.26,-.52,3.02));radius=.78
samples=[];p=Vector();v=Vector();memory=Vector();dt=1/24
for frame in range(1,241):
 t=(frame-1)/24;held=.5<=t<1.8 or 4.4<=t<5.8;target=Vector((0,.48,-.04)) if .5<=t<1.8 else Vector((.90,-.25,.12)) if 4.4<=t<5.8 else Vector()
 w=24 if held else 12;zeta=.68 if held else .19;a=zeta*w;b=w*math.sqrt(1-zeta*zeta);e=math.exp(-a*dt);cs=math.cos(b*dt);sn=math.sin(b*dt);goal=target*.82;x=p-goal
 p=goal+e*(x*cs+(v+a*x)*sn/b);v=e*(v*cs-(a*v+w*w*x)*sn/b);memory+=(target*.18-memory)*(1-math.exp(-dt/(.5 if held else 5/3.4)));d=p+memory;samples.append((frame,d.copy(),max(0,d.y)))
o.shape_key_add(name='Rest')
for axis in range(4):
 k=o.shape_key_add(name=['Local X','Local depth','Local height','Local bulge'][axis]);k.slider_min=-2;k.slider_max=2
 for vertex in k.data:
  q=vertex.co-center;weight=max(0,1-q.length_squared/radius**2)**3
  if axis<3:vertex.co[axis]+=weight
  else:vertex.co.x+=q.x*weight*.35/radius;vertex.co.z+=q.z*weight*.35/radius
 for f,d,bulge in samples:k.value=d[axis] if axis<3 else bulge;k.keyframe_insert(data_path='value',frame=f)
 k.value=0
o['method']='Closed projected-texture volume. Front appearance from original; hidden geometry/back inferred. Local viscoelastic animation, not FEM.'
bpy.ops.object.camera_add(location=(0,-12,2.05));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,2.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.75
for loc,power,size in [((-3,-4,7),120,5),((4,-1,5),80,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,2))-l.location).to_track_quat('-Z','Y').to_euler()
s=bpy.context.scene;s.camera=cam;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32;s.render.resolution_x=800;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard';s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25;s.render.fps=24;s.frame_end=240;s.frame_set(1)
for label,f in [('Rest - source silhouette',1),('Local press',20),('Release',44),('Pull cheek',116),('Release pull',140)]:s.timeline_markers.new(label,frame=f)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'blender','toy.blend'),compress=True)
s.render.filepath=os.path.join(ROOT,'renders','preview.png');bpy.ops.render.render(write_still=True)
print('REFERENCE_MODEL_COMPLETE',len(me.vertices))
