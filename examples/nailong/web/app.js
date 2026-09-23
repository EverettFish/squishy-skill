import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {FoamMode,JellyMode,deformPoint,squashFactors} from './physics.js';

const $=s=>document.querySelector(s),viewport=$('#viewport');
let config={name:'奶龙',model:'./assets/nailong.glb'};
try{const r=await fetch('./toy.json');if(r.ok)config={...config,...await r.json()};}catch{}
$('#toyName').textContent=config.name;document.title=config.name+'捏捏';
const english=config.language==='en';
const words=english?{rest:'Take your time. There is no rush.',press:'A little softer. That is enough.',returning:'Shh… give it a little time.',hint:'Hold it. Then let go.',orbit:'A different angle. The same little friend.',rotate:'Rotate',touch:'Squeeze',soft:'Soft and squishy',cloud:'Like a cloud',firm:'A little firmer'}:{rest:'慢慢来，也没关系',press:'软下来，就好。',returning:'嘘… 给它一点点时间。',hint:'捏一下，再松手。',orbit:'换个角度，看看它。',rotate:'转一转',touch:'捏一捏',soft:'软乎乎',cloud:'像云一样',firm:'绵实一点'};
if(english){document.documentElement.lang='en';document.title=config.name+' · Squishy';$('#loading').textContent='Your little soft friend is on its way…';$('#hint').textContent=words.hint;$('#squeezeButton').textContent='Hold to squeeze';$('[data-mode]').textContent=words.rotate;$('.settings summary').textContent='Feel';$('.settings summary').setAttribute('aria-label','Adjust softness');$('label[for=recovery]').firstChild.textContent='Slow return ';$('label[for=softness]').firstChild.textContent='Softness ';$('#softnessValue').textContent=words.soft;$('#demo').textContent='Watch it recover';$('#viewReset').textContent='Reset view';$('#viewReset').setAttribute('aria-label','Reset view');const copy=document.querySelectorAll('.gentle-copy p');copy[0].textContent='A little softer. A little slower.';copy[1].textContent='A few seconds, just for you.';$('#state').textContent=words.rest;viewport.setAttribute('aria-label','Drag the toy to press it. Toggle rotation to look around. Hold Space to squeeze.');}
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});}catch(e){$('#loading').textContent='当前浏览器未能启动 3D。请启用硬件加速后刷新。';$('#loading').className='error';throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
viewport.append(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(32,1,.1,70);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=5;controls.maxDistance=14;controls.minPolarAngle=.25;controls.maxPolarAngle=Math.PI*.49;controls.enabled=false;
const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;room.dispose();pmrem.dispose();scene.environmentIntensity=.45;
scene.add(new THREE.HemisphereLight(0xfffbe9,0xa0ac83,2.2));
const key=new THREE.DirectionalLight(0xfff9e8,2.5);key.position.set(-3,7,5);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-5;key.shadow.camera.right=5;key.shadow.camera.top=6;key.shadow.camera.bottom=-4;key.shadow.normalBias=.015;key.shadow.bias=-.0002;key.shadow.radius=5;scene.add(key);
const fill=new THREE.DirectionalLight(0xffffff,1.4);fill.position.set(4,3,-2);scene.add(fill);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.ShadowMaterial({opacity:0}));floor.rotation.x=-Math.PI/2;floor.position.y=.005;floor.receiveShadow=false;scene.add(floor);
// Soft contact shadow, generated as a mathematical opacity field.
const shadowData=new Uint8Array(128*128*4);
for(let y=0;y<128;y++)for(let x=0;x<128;x++){const i=(y*128+x)*4,d=((x-64)/42)**2+((y-64)/42)**2;shadowData[i]=57;shadowData[i+1]=67;shadowData[i+2]=38;shadowData[i+3]=Math.round(43*Math.exp(-d*2.1));}
const shadowTexture=new THREE.DataTexture(shadowData,128,128);shadowTexture.needsUpdate=true;
const shadow=new THREE.Mesh(new THREE.PlaneGeometry(3.4,2.5),new THREE.MeshBasicMaterial({map:shadowTexture,transparent:true,depthWrite:false}));shadow.rotation.x=-Math.PI/2;shadow.position.y=.014;scene.add(shadow);
// Dense, subtle foam pores. All files, including Three.js, are local/offline-capable.
const poreData=new Uint8Array(256*256*4);let seed=78251;
for(let i=0;i<256*256;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const n=seed/4294967296;const v=n>.94?95:170+Math.floor(n*55);poreData.set([v,v,v,255],i*4);}
const pores=new THREE.DataTexture(poreData,256,256);pores.wrapS=pores.wrapT=THREE.RepeatWrapping;pores.repeat.set(7,7);pores.magFilter=THREE.LinearFilter;pores.minFilter=THREE.LinearMipmapLinearFilter;pores.generateMipmaps=true;pores.needsUpdate=true;
const meshes=[];let ready=false,mode='press',softness=.75,recovery=6,holding=false,source=null,activeDent=null,load=.85,demoTimer=null,dragStart=0;
const globalMode=new FoamMode(),jelly=new JellyMode(),dents=[],raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let model,toyHeight=4.1;
function home(){const mobile=viewport.clientWidth<760;const distance=mobile?Math.max(11,7.0/Math.max(.4,camera.aspect)):11.5;camera.position.set(distance*.29,toyHeight*.74,distance*.96);controls.target.set(0,toyHeight*(mobile?.33:.44),0);controls.update();}
function resize(){renderer.setSize(viewport.clientWidth,viewport.clientHeight);camera.aspect=viewport.clientWidth/viewport.clientHeight;camera.updateProjectionMatrix();if(ready)home();}
new ResizeObserver(resize).observe(viewport);home();resize();
new GLTFLoader().load(config.model,gltf=>{
  model=gltf.scene;model.updateMatrixWorld(true);
  const bounds=new THREE.Box3().setFromObject(model),size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());
  const scale=Math.min(4.1/Math.max(size.y,.001),3.6/Math.max(size.x,.001),3.8/Math.max(size.z,.001));toyHeight=size.y*scale;
  const normalize=new THREE.Matrix4().makeScale(scale,scale,scale);normalize.setPosition(-center.x*scale,-bounds.min.y*scale+.026,-center.z*scale);
  const nodes=[];model.traverse(o=>{if(o.isMesh)nodes.push(o);});
  if(!nodes.length){$('#loading').textContent=english?'This model contains no visible toy. Please check the exported file.':'模型中没有可显示的玩具，请检查导出文件。';return;}
  for(const o of nodes){
    const geom=o.geometry.clone();geom.applyMatrix4(normalize.clone().multiply(o.matrixWorld));geom.computeVertexNormals();geom.boundingBox=null;
    const original=o.material;const foam=/foam|mango|vanilla|peach/i.test(original.name);
    const material=new THREE.MeshPhysicalMaterial({color:original.color,map:original.map,normalMap:original.normalMap,roughnessMap:original.roughnessMap,alphaMap:original.alphaMap,transparent:original.transparent,opacity:original.opacity,vertexColors:!!geom.attributes.color,roughness:foam?.88:original.roughness,metalness:0,side:THREE.DoubleSide,envMapIntensity:foam?.4:.75,sheen:foam?.22:0,sheenColor:0xffd577,sheenRoughness:.85,clearcoat:foam?0:.12,clearcoatRoughness:.5});
    if(foam&&!original.normalMap){material.bumpMap=pores;material.bumpScale=.014;}
    const mesh=new THREE.Mesh(geom,material);mesh.name=o.name;mesh.castShadow=true;mesh.receiveShadow=true;mesh.frustumCulled=false;
    mesh.userData.rest=geom.attributes.position.array.slice();scene.add(mesh);meshes.push(mesh);
  }
  ready=true;home();$('#loading').remove();$('#squeezeButton').disabled=false;$('#demo').disabled=false;$('#state').textContent=words.rest;
},undefined,e=>{console.error(e);$('#loading').textContent=english?'Your toy could not load. Please refresh and try again.':'小捏捏暂时没加载出来。请刷新页面重试。';$('#loading').className='error';});

function setMode(next){release();mode=next;controls.enabled=next==='rotate';document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('selected',b.dataset.mode===next);b.setAttribute('aria-pressed',b.dataset.mode===next);b.textContent=next==='rotate'?words.touch:words.rotate;});$('#hint').textContent=next==='rotate'?words.orbit:words.hint;}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(mode==='rotate'?'press':'rotate')));
function release(){if(holding)jelly.kick(Math.max(globalMode.value,activeDent?activeDent.mode.value*activeDent.strength*.7:0));holding=false;source=null;activeDent=null;viewport.classList.remove('pressing');$('#squeezeButton').classList.remove('active');}
function beginGlobal(from='button'){if(!ready)return;clearTimeout(demoTimer);release();holding=true;source=from;load=.88;$('#squeezeButton').classList.add('active');}
function pressHit(e){const r=viewport.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(meshes,false)[0];}
viewport.addEventListener('pointerdown',e=>{
  if(!ready||mode==='rotate'||e.button!==0)return;
  const hit=pressHit(e);if(!hit)return;e.preventDefault();clearTimeout(demoTimer);release();holding=true;source='model';dragStart=e.clientY;load=.68;viewport.setPointerCapture(e.pointerId);viewport.classList.add('pressing');
  if(mode==='press'){
    // Map the selected deformed triangle back to its rest coordinates.
    const mesh=hit.object,g=mesh.geometry,rest=mesh.userData.rest;
    const ia=hit.face.a,ib=hit.face.b,ic=hit.face.c;
    const a=new THREE.Vector3().fromBufferAttribute(g.attributes.position,ia),b=new THREE.Vector3().fromBufferAttribute(g.attributes.position,ib),c=new THREE.Vector3().fromBufferAttribute(g.attributes.position,ic);
    const bary=new THREE.Vector3();THREE.Triangle.getBarycoord(hit.point,a,b,c,bary);
    const center=[0,0,0];for(let i=0;i<3;i++)center[i]=rest[ia*3+i]*bary.x+rest[ib*3+i]*bary.y+rest[ic*3+i]*bary.z;
    const normal=hit.face.normal.clone();if(normal.dot(raycaster.ray.direction)>0)normal.negate();
    if(dents.length>=8)dents.shift();activeDent={center,normal:normal.toArray(),radius:.65+softness*.3,strength:softness,mode:new FoamMode()};dents.push(activeDent);
  }
});
viewport.addEventListener('pointermove',e=>{if(!holding||source!=='model')return;load=THREE.MathUtils.clamp(.68+(e.clientY-dragStart)/180,.2,1);if(e.pressure>.1&&e.pointerType==='pen')load=e.pressure;});
viewport.addEventListener('pointerup',release);viewport.addEventListener('pointercancel',release);viewport.addEventListener('lostpointercapture',release);
const sq=$('#squeezeButton');sq.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();sq.setPointerCapture(e.pointerId);beginGlobal();});sq.addEventListener('pointerup',release);sq.addEventListener('pointercancel',release);sq.addEventListener('lostpointercapture',release);
sq.addEventListener('keydown',e=>{if(e.code==='Enter'&&!e.repeat){e.preventDefault();beginGlobal('key');}});sq.addEventListener('keyup',e=>{if(e.code==='Enter')release();});
window.addEventListener('keydown',e=>{if(e.code==='Space'&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();if(!e.repeat)beginGlobal('key');}});window.addEventListener('keyup',e=>{if(e.code==='Space'&&source==='key')release();});window.addEventListener('blur',release);document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
function demonstrate(){beginGlobal('demo');demoTimer=setTimeout(release,1450);}
$('#demo').addEventListener('click',demonstrate);$('#viewReset').addEventListener('click',home);
for(const id of ['recovery','softness']){$('#'+id).addEventListener('input',e=>{if(id==='recovery'){recovery=+e.target.value;$('#recoveryValue').textContent=recovery.toFixed(1)+' s';}else{softness=+e.target.value;$('#softnessValue').textContent=softness>.8?words.cloud:softness>.5?words.soft:words.firm;}rangePaint(e.target);});rangePaint($('#'+id));}
function rangePaint(el){const p=(el.value-el.min)/(el.max-el.min)*100;el.style.background=`linear-gradient(to right,#d4b642 ${p}%,#eeeee8 ${p}%)`;}
let previous=performance.now(),normalFrame=0,lastState='',lastAmount=0;const temp=[0,0,0];
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,.05);previous=now;controls.update();
  if(ready){
    const squeeze=holding&&(!activeDent)&&(source!=='model'||mode==='squeeze');
    const amount=globalMode.step(dt,squeeze?load*softness:0,recovery);
    let maxDent=0;for(const d of dents){d.mode.step(dt,holding&&d===activeDent?load:0,recovery);maxDent=Math.max(maxDent,d.mode.value*d.strength);}
    for(let i=dents.length-1;i>=0;i--)if(dents[i]!==activeDent&&dents[i].mode.value===0)dents.splice(i,1);
    const jiggle=jelly.step(dt),total=Math.max(amount,maxDent,Math.abs(jiggle));
    if(total>0||lastAmount>0){
      for(const mesh of meshes){const pos=mesh.geometry.attributes.position,rest=mesh.userData.rest,arr=pos.array;
        for(let i=0;i<arr.length;i+=3){deformPoint(rest[i],rest[i+1],rest[i+2],amount,dents,temp,jiggle);arr[i]=temp[0];arr[i+1]=temp[1];arr[i+2]=temp[2];}
        pos.needsUpdate=true;if(normalFrame%2===0||total===0)mesh.geometry.computeVertexNormals();
        // Updated bounds keep raycasting reliable throughout large deformation.
        mesh.geometry.computeBoundingSphere();
      }normalFrame++;
    }
    lastAmount=total;shadow.scale.setScalar(1+amount*.28);
    const state=holding?words.press:total>.012?words.returning:words.rest;
    if(state!==lastState){$('#state').textContent=state;lastState=state;}
  }renderer.render(scene,camera);
}requestAnimationFrame(animate);
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();release();const n=document.createElement('div');n.id='loading';n.textContent='3D 画面暂时中断，请刷新页面恢复。';viewport.append(n);});
// Optional browser-standard agent controls use the same visible settings/actions.
if(document.modelContext?.registerTool){
  const life=new AbortController();
  for(const tool of [
    {name:'read_squishy_state',description:'Read current toy state and recovery settings.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:()=>({ready,mode,recoverySeconds:recovery,softness,compression:globalMode.value})},
    {name:'set_squishy_recovery',description:'Set visible slow recovery time from 2 to 12 seconds.',inputSchema:{type:'object',properties:{seconds:{type:'number',minimum:2,maximum:12}},required:['seconds'],additionalProperties:false},execute:({seconds})=>{if(!Number.isFinite(seconds)||seconds<2||seconds>12)throw Error('seconds must be 2–12');$('#recovery').value=Math.round(seconds*2)/2;$('#recovery').dispatchEvent(new Event('input'));return {recoverySeconds:recovery};}}
  ]){try{Promise.resolve(document.modelContext.registerTool(tool,{signal:life.signal})).catch(()=>{});}catch{}}
  window.addEventListener('pagehide',()=>life.abort(),{once:true});
}
