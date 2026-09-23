import bpy, math, os, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'web', 'assets')
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=.75, foam=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    if foam:
        p.inputs['Subsurface Weight'].default_value=.12
        p.inputs['Subsurface Radius'].default_value=(1,.55,.23)
        p.inputs['Sheen Weight'].default_value=.16
        n=m.node_tree.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=155; n.inputs['Detail'].default_value=2
        b=m.node_tree.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.2; b.inputs['Distance'].default_value=.014
        m.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']); m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
    return m
yellow=mat('Mango • microcellular polyurethane',(1,.52,.012),.8,True)
cream=mat('Vanilla belly',(1,.91,.42),.85,True)
white=mat('Warm ivory',(1,.98,.84),.5)
green=mat('Emerald iris',(.12,.37,.018),.34)
rim=mat('Olive iris rim',(.13,.22,.018),.65)
black=mat('Dark chocolate pupils',(.012,.016,.008),.23)
mouthmat=mat('Smile',(.10,.022,.011),.75)
pink=mat('Peach pads',(1,.30,.13),.84,True)
tongue=mat('Strawberry tongue',(.5,.09,.08),.8)
claw=mat('Cocoa toes',(.32,.15,.045),.85)
parts=[]
def ell(name,loc,scale,m,power=1,segments=48,rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=bpy.context.object; o.name=name
    if power != 1:
        for v in o.data.vertices:
            for i in range(3): v.co[i]=math.copysign(abs(v.co[i])**power,v.co[i])
    o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o); return o
# All silhouettes authored in Blender; front is -Y, vertical is +Z.
body=ell('Body',(0,0,.95),(1.10,.96,.94),yellow)
for v in body.data.vertices:
    t=v.co.z/.94; v.co.x*=1-.04*t; v.co.y*=1-.04*t
head=ell('Head',(0,-.035,2.28),(1.28,1.13,1.16),yellow,.90)
f1=ell('Left foot',(-.59,-.10,.16),(.39,.47,.17),yellow,.7)
f2=ell('Right foot',(.59,-.10,.16),(.39,.47,.17),yellow,.7)
a1=ell('Left little arm',(-1.095,-.06,1.13),(.25,.32,.34),yellow)
a1.rotation_euler[1]=.43
a2=ell('Right little arm',(1.095,-.06,1.13),(.25,.32,.34),yellow); a2.rotation_euler[1]=-.43
tail=[]
for i in range(9):
    t=i/8; tail.append(ell('Tail segment',(-.10*t,.64+.92*t,.46+.08*t+.56*t*t),(.39*(1-t)+.045,.35*(1-t)+.055,.34*(1-t)+.055),yellow,segments=24,rings=16))
# Voxel union yields a continuous foam core, with no disconnected primitive seams.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body; bpy.ops.object.convert(target='MESH'); bpy.ops.object.join()
body.name='Nailong • continuous foam core'
rem=body.modifiers.new('Watertight voxel union','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.038; rem.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=rem.name)
sm=body.modifiers.new('Soft silhouette','SMOOTH'); sm.factor=1.4; sm.iterations=5; bpy.ops.object.modifier_apply(modifier=sm.name)
sub=body.modifiers.new('Surface refinement','SUBSURF'); sub.levels=1; bpy.ops.object.modifier_apply(modifier=sub.name)
parts=[body]
# Project the paint onto the remeshed surface so it never intersects the core.
bpy.context.view_layer.update()
bvh=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
def front_y(x,z,offset=.012):
    hit=bvh.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
    return hit[0].y-offset if hit[0] else -.8
# Belly follows the actual pear surface as a thin painted patch.
verts=[(0,front_y(0,.81),.81)]; faces=[]
nr=18; ns=64
for j in range(1,nr+1):
    r=j/nr
    for i in range(ns):
        a=2*math.pi*i/ns; x=.73*r*math.cos(a); z=.81+.64*r*math.sin(a)
        t=(z-1.38)/1.2; sx=.89*(1-.13*t); sy=.65*(1-.08*t)
        y=front_y(x,z)
        verts.append((x,y,z))
for i in range(ns):faces.append((0,1+i,1+(i+1)%ns))
for j in range(nr-1):
    for i in range(ns):
        a=1+j*ns+i;b=1+j*ns+(i+1)%ns;faces.append((a,a+ns,b+ns,b))
mesh=bpy.data.meshes.new('Belly patch');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('Vanilla belly paint',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(cream);parts.append(o)
for p in mesh.polygons:p.use_smooth=True
def patch(name,x,z,rx,rz,m,offset=.025):
    vs=[(x,front_y(x,z,offset),z)];fs=[];ns=48;nr=12
    for j in range(1,nr+1):
        for i in range(ns):
            a=2*math.pi*i/ns;px=x+rx*j/nr*math.cos(a);pz=z+rz*j/nr*math.sin(a)
            vs.append((px,front_y(px,pz,offset+.01*(1-(j/nr)**2)),pz))
    for i in range(ns):fs.append((0,1+i,1+(i+1)%ns))
    for j in range(nr-1):
        for i in range(ns):
            a=1+j*ns+i;b=1+j*ns+(i+1)%ns;fs.append((a,a+ns,b+ns,b))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);obj.data.materials.append(m);parts.append(obj)
    for p in me.polygons:p.use_smooth=True
for side in [-1,1]:
    x=side*.52;z=2.43
    patch('Eye ivory',x,z,.224,.239,white,.019)
    patch('Eye olive outline',x,z,.203,.222,rim,.025)
    patch('Eye green iris',x,z,.191,.211,green,.031)
    patch('Eye pupil',x,z,.163,.181,black,.040)
    patch('Eye sparkle',x-.036,z+.082,.035,.038,white,.048)
    patch('Eye small sparkle',x+.043,z-.081,.012,.014,white,.048)
    patch('Palm pad',side*1.13,1.02,.105,.134,pink,.019)
    for i in range(3):
        patch('Cocoa toe',side*.59+(i-1)*.17,.10,.066,.058,claw,.023)
        x=side*(1.225+.005*i);z=1.23-.115*i
        patch('Little fingertips',x,z,.061,.071,claw,.025)
# A curved open smile patch, flush to the face; all details deform with foam.
vs=[];fs=[];nx=40;ny=10
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        x=-.40+.8*i/nx; a=x/.4
        top=2.03-.038*(1-a*a); bottom=2.03-.29*math.sqrt(max(0,1-a*a)); z=top*(1-t)+bottom*t
        vs.append((x,front_y(x,z,.019),z))
for j in range(ny):
    for i in range(nx):
        a=j*(nx+1)+i; fs.append((a,a+1,a+nx+2,a+nx+1))
mesh=bpy.data.meshes.new('Smile');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new('Happy smile',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mouthmat);parts.append(o)
def face_paint(name,width,top,bottom,m,offset):
    vertices=[];polys=[]
    for j in range(7):
        t=j/6
        for i in range(41):
            a=-1+2*i/40;x=width*a
            z=top(a)*(1-t)+bottom(a)*t
            vertices.append((x,front_y(x,z,offset),z))
    for j in range(6):
        for i in range(40):
            a=j*41+i;polys.append((a,a+1,a+42,a+41))
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],polys);me.update()
    obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);obj.data.materials.append(m);parts.append(obj)
    for p in me.polygons:p.use_smooth=True
face_paint('Creamy smile edge',.389,lambda a:2.03-.036*(1-a*a),lambda a:2.03-.084*math.sqrt(max(0,1-a*a)),white,.023)
face_paint('Strawberry tongue',.185,lambda a:1.77+.063*math.sqrt(max(0,1-a*a)),lambda a:1.75+.02*a*a,tongue,.026)
# Apply transforms before the common deformation field.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
samples=[];fast=0;slow=0;jiggle=0;velocity=0;last_load=0;dt=1/24
for frame in range(1,242):
    t=(frame-1)/24;load=.95 if .5<=t<2.0 else 0
    if last_load>0 and load==0:velocity+=(.3*fast+.7*slow)*8
    fast+=(load-fast)*(1-math.exp(-dt/(.075 if load>fast else .33)))
    slow+=(load-slow)*(1-math.exp(-dt/(.65 if load>slow else 6/3.4)))
    w=13;d=.24*w;b=w*math.sqrt(1-.24**2);e=math.exp(-d*dt);c=math.cos(b*dt);sn=math.sin(b*dt)
    old=jiggle;jiggle=e*(old*c+(velocity+d*old)*sn/b);velocity=e*(velocity*c-(d*velocity+w*w*old)*sn/b)
    samples.append((frame,.3*fast+.7*slow,jiggle));last_load=load
for o in parts:
    o.shape_key_add(name='Rest')
    k=o.shape_key_add(name='01 - Squash and slow rise')
    for v in k.data:
        z=v.co.z; v.co.z=z*.52; v.co.x*=1.235; v.co.y*=1.235
    q=o.shape_key_add(name='02 - Q elastic jiggle');q.slider_min=-1
    for v in q.data:
        v.co.x*=.86;v.co.y*=.86;v.co.z*=1.22
    # Sampled slow foam memory + damped elastic skin, not a soft-body solver.
    for frame,compression,jiggle in samples:
        k.value=compression;k.keyframe_insert(data_path='value',frame=frame)
        q.value=jiggle*(1-.48*compression);q.keyframe_insert(data_path='value',frame=frame)
    k.value=0;q.value=0
    o['deformation']='Common-space foam deformation; see web/physics.js for interactive constitutive model'
bpy.context.scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'toy.glb'),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_yup=True)
# Studio scene remains in .blend, excluded from GLB.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.06));floor=bpy.context.object;floor.name='Studio floor';floor.data.materials.append(mat('Studio background',(1,1,1),.9))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Large softbox',(-3,-4,7),650,5),('Fill',(4,-1,5),420,4),('Rim',(0,4,6),800,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,2))
bpy.ops.object.camera_add(location=(4.2,-11,4.5));cam=bpy.context.object;aim(cam,(0,0,1.72));cam.data.type='ORTHO';cam.data.ortho_scale=4.75
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.85,.85,.85,1);s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7
s.view_settings.view_transform='AgX';s.render.fps=24;s.frame_end=241
for label,frame in [('Rest',1),('Hold - squash',13),('Release - Q jiggle',49),('Slow rise',84),('Rest again',241)]:s.timeline_markers.new(label,frame=frame)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=6.2;area.spaces.active.region_3d.view_location=(0,0,1.6);area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion();area.spaces.active.shading.color_type='MATERIAL'
s['Material model']='Illustrative viscoelastic slow-rising PU foam; not measured material data or FEM'
s.render.filepath=os.path.join(ROOT,'preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'toy.blend'))
bpy.ops.render.render(write_still=True)
print('NAILONG_EXPORT_COMPLETE')

