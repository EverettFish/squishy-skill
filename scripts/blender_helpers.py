"""Small reusable Blender building blocks. Import from your subject's build script."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def gel_material(name='Gel',color=(.04,.18,.55),roughness=.32):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    for key,value in {'Base Color':(*color,1),'Roughness':roughness,'Metallic':0,'Subsurface Weight':.13,'Subsurface Radius':(1,.45,.22),'Coat Weight':.38,'Coat Roughness':.25}.items():p.inputs[key].default_value=value
    return m

def studio_scene(target=(0,0,1.7),ortho_scale=4.4,preview=True):
    """Create lights/camera/world; exclude them from the toy export."""
    def aim(o):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    for location,power,size in [((-3,-4,7),550,4),((4,-1,5),350,3),((0,4,6),650,3)]:
        bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o)
    bpy.ops.object.camera_add(location=(3.4,-12,4.4));cam=bpy.context.object;aim(cam);cam.data.type='ORTHO';cam.data.ortho_scale=ortho_scale
    s=bpy.context.scene;s.camera=cam;s.render.engine='BLENDER_EEVEE_NEXT' if preview else 'CYCLES'
    if preview:s.eevee.taa_render_samples=16
    else:s.cycles.samples=32;s.cycles.use_denoising=True
    s.render.resolution_x=520 if preview else 900;s.render.resolution_y=560 if preview else 1000;s.render.resolution_percentage=100
    if s.world is None:s.world=bpy.data.worlds.new('Studio world')
    s.world.use_nodes=True;p=s.world.node_tree.nodes.get('Background');p.inputs['Color'].default_value=(1,1,1,1);p.inputs['Strength'].default_value=.65
    s.view_settings.view_transform='AgX';s.render.fps=24
    return s

def foam_material(name='Foam',color=(1,.55,.04),roughness=.84):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness
    p.inputs['Subsurface Weight'].default_value=.12;p.inputs['Subsurface Radius'].default_value=(1,.5,.25);p.inputs['Sheen Weight'].default_value=.15
    n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=155
    b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.18;b.inputs['Distance'].default_value=.01
    m.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
    return m

def ellipsoid(name,location,scale,material,segments=48,rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=location)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    for poly in o.data.polygons:poly.use_smooth=True
    return o

def union_foam(objects,voxel=.05,smooth=5,subdivision=1):
    if not objects:raise ValueError('At least one mesh is required')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();o=bpy.context.object
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    r=o.modifiers.new('Continuous foam core','REMESH');r.mode='VOXEL';r.voxel_size=voxel;r.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=r.name)
    s=o.modifiers.new('Soft joins','SMOOTH');s.factor=1.2;s.iterations=smooth;bpy.ops.object.modifier_apply(modifier=s.name)
    if subdivision:
        s=o.modifiers.new('Smooth surface','SUBSURF');s.levels=subdivision;bpy.ops.object.modifier_apply(modifier=s.name)
    return o

def surface_projector(core):
    bpy.context.view_layer.update()
    tree=BVHTree.FromPolygons([core.matrix_world@v.co for v in core.data.vertices],[list(p.vertices) for p in core.data.polygons])
    def project(origin,direction,offset=.01):
        hit,normal,index,distance=tree.ray_cast(Vector(origin),Vector(direction))
        if hit is None:raise ValueError('Surface projection missed the core')
        return hit+normal*offset
    return project

def export_toy(objects,blend_path,glb_path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(glb_path),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
