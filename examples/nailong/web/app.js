import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {GelContact,contactKernel,applyGel} from './physics.js';

const $=s=>document.querySelector(s),viewport=$('#viewport');
let config={name:'小捏捏',model:'./assets/toy.glb',language:'zh',material:'gel',accent:'#5385d9'};
try{const r=await fetch('./toy.json');if(r.ok)config={...config,...await r.json()};}catch{}
const en=config.language==='en';
const text=en?{press:'Press',pull:'Pull',rotate:'Rotate',feel:'Feel',rest:'Take your time. There is no rush.',holding:'Soft enough to let go.',release:'A little wobble. A little breather.',hint:'Hold a spot. Drag to squish.',pullHint:'Grab a little bit. Pull it out.',orbit:'A different angle, just for a moment.',loading:'Your little soft friend is on its way…',error:'The toy could not load. Refresh to try again.'}:{press:'按压',pull:'拉扯',rotate:'转一转',feel:'手感',rest:'慢慢来，也没关系',holding:'软软的，怎么揉都没关系。',release:'晃一晃，再慢慢回来。',hint:'按住一点，拖动揉捏。',pullHint:'抓住一点，往外拉。',orbit:'换个角度，看看它。',loading:'软乎乎的它，马上就来…',error:'小捏捏暂时没加载出来，请刷新重试。'};
document.documentElement.lang=en?'en':'zh-CN';document.title=config.name+(en?' · Squishy':'捏捏');$('#toyName').textContent=config.name;$('#hint').textContent=text.hint;$('#loading').textContent=text.loading;$('#state').textContent=text.rest;
document.documentElement.style.setProperty('--accent',config.accent);document.querySelectorAll('[data-mode]').forEach(b=>b.textContent=text[b.dataset.mode]);$('.settings summary').textContent=text.feel;
if(en){$('label[for=recovery]').firstChild.textContent='Slow return ';$('label[for=softness]').firstChild.textContent='Stretchiness ';$('#demo').textContent='Try a little pull';$('#viewReset').textContent='Reset view';const p=document.querySelectorAll('.gentle-copy p');p[0].textContent='A little softer. A little slower.';p[1].textContent='A few seconds, just for you.';}
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});}catch(e){$('#loading').textContent=en?'Enable hardware acceleration and refresh to play.':'请启用浏览器硬件加速后刷新。';throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;viewport.append(renderer.domElement);
const scene=new THREE.Scene(),camera=config.referenceTexture?new THREE.OrthographicCamera(-3,3,3,-3,.1,60):new THREE.PerspectiveCamera(32,1,.1,60);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.minZoom=.65;orbit.maxZoom=2.4;orbit.enableDamping=true;orbit.enablePan=false;orbit.enabled=false;orbit.minDistance=5;orbit.maxDistance=17;orbit.maxPolarAngle=Math.PI*.49;
const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.035).texture;scene.environmentIntensity=.55;room.dispose();pmrem.dispose();
scene.add(new THREE.HemisphereLight(0xfffaf4,0xc8d2ea,2.2));
for(const [color,power,pos] of [[0xfff8ef,2.4,[-4,7,6]],[0xcce0ff,1.2,[5,4,-2]]]){const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);}
const sd=new Uint8Array(128*128*4);for(let y=0;y<128;y++)for(let x=0;x<128;x++){const i=(y*128+x)*4,d=((x-64)/38)**2+((y-64)/38)**2;sd.set([50,55,70,Math.round(40*Math.exp(-d*2))],i);}
const st=new THREE.DataTexture(sd,128,128);st.needsUpdate=true;const shadow=new THREE.Mesh(new THREE.PlaneGeometry(3.8,3),new THREE.MeshBasicMaterial({map:st,transparent:true,depthWrite:false}));shadow.rotation.x=-Math.PI/2;shadow.position.y=.01;scene.add(shadow);
let ready=false,mode='press',height=4,recovery=5,softness=1,active=null,drag=null,lastMotion=0,frame=0,lastState='',lastTime=performance.now(),timer=null;
const meshes=[],contacts=[],ray=new THREE.Raycaster(),pointer=new THREE.Vector2(),plane=new THREE.Plane(),world=new THREE.Vector3();
function home(){const mobile=viewport.clientWidth<760,d=mobile?Math.max(11.5,7.2/Math.max(camera.aspect,.35)):11.8;if(config.referenceTexture){const a=viewport.clientWidth/viewport.clientHeight,span=mobile?Math.max(height*1.6,2.9/a):height*1.43;camera.left=-span*a/2;camera.right=span*a/2;camera.top=span/2;camera.bottom=-span/2;camera.zoom=1;camera.updateProjectionMatrix();camera.position.set(0,height*(mobile?.38:.46),12);orbit.target.set(0,height*(mobile?.38:.46),0);}else{camera.position.set(d*.20,height*.74,d*.98);orbit.target.set(0,height*(mobile?.34:.44),0);}orbit.update();}
function resize(){renderer.setSize(viewport.clientWidth,viewport.clientHeight);camera.aspect=viewport.clientWidth/viewport.clientHeight;camera.updateProjectionMatrix();if(ready)home();}
new ResizeObserver(resize).observe(viewport);resize();home();
new GLTFLoader().load(config.model,gltf=>{
  const model=gltf.scene;model.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(model),size=box.getSize(new THREE.Vector3()),c=box.getCenter(new THREE.Vector3());
  const s=Math.min(4.1/Math.max(size.y,.001),3.65/Math.max(size.x,.001),3.9/Math.max(size.z,.001));height=size.y*s;const normalize=new THREE.Matrix4().makeScale(s,s,s);normalize.setPosition(-c.x*s,-box.min.y*s+.025,-c.z*s);
  model.traverse(o=>{if(!o.isMesh)return;const g=o.geometry.clone();g.applyMatrix4(normalize.clone().multiply(o.matrixWorld));g.boundingBox=null;g.computeVertexNormals();
    const m=o.material,eye=/pupil|iris|eye|sparkle/i.test(m.name),gel=config.material!=='foam';
    const material=new THREE.MeshPhysicalMaterial({color:m.color,map:m.map,normalMap:m.normalMap,vertexColors:!!g.attributes.color,roughness:eye?.22:gel?.33:.8,metalness:0,clearcoat:gel?.48:.08,clearcoatRoughness:.28,sheen:gel?.06:.2,sheenColor:0xffdfd0,envMapIntensity:eye?.65:gel?.4:.2,side:THREE.DoubleSide});
    if(config.referenceTexture){material.color.setRGB(0,0,0);material.map=null;material.emissive.setRGB(1,1,1);material.emissiveMap=m.map||m.emissiveMap;material.emissiveIntensity=1;material.toneMapped=false;material.clearcoat=.10;material.clearcoatRoughness=.3;material.roughness=.48;material.envMapIntensity=.15;addReferenceShading(material,g);}const mesh=new THREE.Mesh(g,material);mesh.name=o.name;mesh.frustumCulled=false;mesh.userData={rest:g.attributes.position.array.slice(),kernels:[]};scene.add(mesh);meshes.push(mesh);
  });
  if(!meshes.length){$('#loading').textContent=text.error;return;}
  ready=true;home();$('#loading').remove();document.querySelectorAll('button[disabled]').forEach(b=>b.disabled=false);
},undefined,e=>{console.error(e);$('#loading').textContent=text.error;});
function cast(clientX,clientY){const b=viewport.getBoundingClientRect();pointer.set((clientX-b.left)/b.width*2-1,1-(clientY-b.top)/b.height*2);ray.setFromCamera(pointer,camera);return ray.intersectObjects(meshes,false)[0];}
function restPoint(hit){const g=hit.object.geometry,r=hit.object.userData.rest,f=hit.face,a=new THREE.Vector3().fromBufferAttribute(g.attributes.position,f.a),b=new THREE.Vector3().fromBufferAttribute(g.attributes.position,f.b),c=new THREE.Vector3().fromBufferAttribute(g.attributes.position,f.c),bary=new THREE.Vector3();THREE.Triangle.getBarycoord(hit.point,a,b,c,bary);return [0,1,2].map(i=>r[f.a*3+i]*bary.x+r[f.b*3+i]*bary.y+r[f.c*3+i]*bary.z);}
function dropContact(contact){const i=contacts.indexOf(contact);if(i>=0)contacts.splice(i,1);for(const m of meshes)m.userData.kernels=m.userData.kernels.filter(k=>k.contact!==contact);}
function begin(hit,kind=mode){release();if(contacts.length>=5){const oldest=contacts.find(c=>!c.active);if(oldest)dropContact(oldest);}
  const normal=hit.face.normal.clone();if(normal.dot(ray.ray.direction)>0)normal.negate();
  active=new GelContact(restPoint(hit),normal.toArray(),(config.contactRadius??1.15)+softness*.12);contacts.push(active);for(const m of meshes)m.userData.kernels.push(contactKernel(m.userData.rest,active));
  active.kind=kind;const base=kind==='pull'?.12:-(config.pressDepth??.70)*softness;const initial=normal.clone().multiplyScalar(base);if(config.referenceTexture&&kind!=="pull")initial.y-=.12*softness;active.setTarget(initial.toArray());
  drag={point:hit.point.clone(),normal,startY:0,kind};plane.setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()),hit.point);viewport.classList.add('pressing');return active;
}
function release(){if(active)active.release();active=null;drag=null;viewport.classList.remove('pressing');}
function setMode(next){clearTimeout(timer);release();mode=next;orbit.enabled=next==='rotate';document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('selected',b.dataset.mode===next);b.setAttribute('aria-pressed',b.dataset.mode===next);});$('#hint').textContent=next==='rotate'?text.orbit:next==='pull'?text.pullHint:text.hint;}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));
viewport.addEventListener('pointerdown',e=>{if(!ready||mode==='rotate'||e.button!==0)return;const hit=cast(e.clientX,e.clientY);if(!hit)return;e.preventDefault();clearTimeout(timer);begin(hit,e.shiftKey?'pull':mode);drag.startY=e.clientY;viewport.setPointerCapture(e.pointerId);});
viewport.addEventListener('pointermove',e=>{if(!active||!drag)return;const b=viewport.getBoundingClientRect();pointer.set((e.clientX-b.left)/b.width*2-1,1-(e.clientY-b.top)/b.height*2);ray.setFromCamera(pointer,camera);if(!ray.ray.intersectPlane(plane,world))return;
  const delta=world.clone().sub(drag.point),n=drag.normal,target=new THREE.Vector3();
  if(drag.kind==='pull'){target.copy(delta).multiplyScalar(1.38*softness).addScaledVector(n,.12+delta.length()*.43*softness);}
  else{const tangent=delta.clone().addScaledVector(n,-delta.dot(n)),down=Math.max(0,(e.clientY-drag.startY)/viewport.clientHeight);target.copy(tangent).multiplyScalar(1.25*softness).addScaledVector(n,-Math.min(1.18,((config.pressDepth??.70)+down*1.7)*softness));}
  if(config.referenceTexture&&drag.kind!=="pull")target.y-=.12*softness;active.setTarget(target.toArray());
});
for(const name of ['pointerup','pointercancel','lostpointercapture'])viewport.addEventListener(name,release);
window.addEventListener('blur',release);document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
function centreContact(kind='press'){const b=viewport.getBoundingClientRect(),hit=cast(b.left+b.width*.50,b.top+b.height*.43);if(hit)return begin(hit,kind);}
window.addEventListener('keydown',e=>{if(e.code==='Space'&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();if(ready&&!e.repeat)centreContact('press');}});window.addEventListener('keyup',e=>{if(e.code==='Space')release();});
$('#viewReset').addEventListener('click',home);
$('#demo').addEventListener('click',()=>{setMode('pull');home();const c=centreContact('pull');if(!c)return;c.setTarget([1.45,.45,.45]);timer=setTimeout(release,2800);});
for(const id of ['recovery','softness']){const el=$('#'+id);el.addEventListener('input',()=>{recovery=+$('#recovery').value;softness=+$('#softness').value;$('#recoveryValue').textContent=recovery.toFixed(1)+' s';$('#softnessValue').textContent=softness>1.1?(en?'Extra stretchy':'超黏弹'):(en?'Jelly-soft':'果冻感');paint(el);});paint(el);}
function paint(el){const p=(el.value-el.min)/(el.max-el.min)*100;el.style.background=`linear-gradient(to right,${config.accent} ${p}%,#ededed ${p}%)`;}
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-lastTime)/1000,.06);lastTime=now;orbit.update();let motion=0;
  if(ready){for(const c of [...contacts]){c.step(dt,recovery);motion=Math.max(motion,c.energy);if(!c.active&&c.energy===0)dropContact(c);}
    if(motion>0||lastMotion>0){for(const m of meshes){const g=m.geometry;applyGel(m.userData.rest,g.attributes.position.array,m.userData.kernels);g.attributes.position.needsUpdate=true;if(frame%2===0||motion===0)g.computeVertexNormals();g.computeBoundingSphere();}frame++;}
    lastMotion=motion;const state=active?text.holding:motion>.008?text.release:text.rest;if(state!==lastState){$('#state').textContent=state;lastState=state;}
  }renderer.render(scene,camera);
}requestAnimationFrame(animate);
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();release();const n=document.createElement('div');n.id='loading';n.textContent=text.error;viewport.append(n);});
if(document.modelContext?.registerTool){const controller=new AbortController();for(const tool of [
  {name:'read_squishy_state',description:'Read local squishy contacts and settings.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:()=>({ready,mode,recoverySeconds:recovery,softness,contacts:contacts.map(c=>({active:c.active,center:c.center,displacement:c.displacement,energy:c.energy}))})},
  {name:'set_squishy_recovery',description:'Set the visible recovery time.',inputSchema:{type:'object',properties:{seconds:{type:'number',minimum:2,maximum:12}},required:['seconds'],additionalProperties:false},execute:({seconds})=>{if(!Number.isFinite(seconds)||seconds<2||seconds>12)throw Error('seconds must be 2–12');$('#recovery').value=Math.round(seconds*2)/2;$('#recovery').dispatchEvent(new Event('input'));return {recoverySeconds:recovery};}}
]){try{Promise.resolve(document.modelContext.registerTool(tool,{signal:controller.signal})).catch(()=>{});}catch{}}window.addEventListener('pagehide',()=>controller.abort(),{once:true});}

// Preserve baked reference colours at rest; shade only changes in surface orientation.
function addReferenceShading(material,geometry){
  geometry.setAttribute('restNormal',new THREE.BufferAttribute(geometry.attributes.normal.array.slice(),3));
  material.onBeforeCompile=shader=>{
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute vec3 restNormal;\nvarying vec3 vSquishRest;\nvarying vec3 vSquishLive;');
    shader.vertexShader=shader.vertexShader.replace('#include <beginnormal_vertex>','#include <beginnormal_vertex>\nvSquishRest=normalize(normalMatrix*restNormal);\nvSquishLive=normalize(normalMatrix*normal);');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vSquishRest;\nvarying vec3 vSquishLive;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <emissivemap_fragment>','#include <emissivemap_fragment>\nvec3 squishLight=normalize(vec3(-.6,.8,1.));\nfloat squishChange=dot(normalize(vSquishLive),squishLight)-dot(normalize(vSquishRest),squishLight);\ntotalEmissiveRadiance*=clamp(1.+squishChange*.75,.48,1.35);');
  };
  material.customProgramCacheKey=()=> 'reference-relative-light-v1';
}