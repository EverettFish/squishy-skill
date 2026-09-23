import test from 'node:test';
import assert from 'node:assert/strict';
import {FoamMode,JellyMode,deformPoint,squashFactors} from '../assets/web/physics.js';
function simulate(hz,hold=2,rest=0,recovery=6){const m=new FoamMode();for(let i=0;i<hold*hz;i++)m.step(1/hz,1,recovery);for(let i=0;i<rest*hz;i++)m.step(1/hz,0,recovery);return m;}
test('long holds creep deeper than short taps',()=>assert.ok(simulate(60,2).value>simulate(60,.2).value+.3));
test('release retains dent, returns monotonically without overshoot',()=>{const m=simulate(60);let last=m.value;m.step(1/60,0,6);assert.ok(m.value>.8);for(let i=0;i<600;i++){m.step(1/60,0,6);assert.ok(m.value<=last&&m.value>=0);last=m.value;}assert.ok(m.value<.004);});
test('frame-rate invariant at 30,60,120 Hz',()=>{const vals=[30,60,120].map(hz=>simulate(hz,2,3).value);assert.ok(Math.max(...vals)-Math.min(...vals)<1e-10);});
test('recovery setting meaningfully changes relaxation',()=>assert.ok(simulate(60,2,3,12).value>simulate(60,2,3,2).value*5));
test('compressible foam expands laterally but loses volume',()=>{const [x,y,z]=squashFactors(1);assert.ok(x>1&&z>1&&y<.6);assert.ok(x*y*z>.65&&x*y*z<1);});
test('local contact dents front without pulling through back',()=>{const d={center:[0,3,.7],normal:[0,0,1],radius:.8,strength:1,mode:{value:1}};const front=deformPoint(0,3,.7,0,[d],[0,0,0]);const back=deformPoint(0,3,-.7,0,[d],[0,0,0]);assert.ok(front[2]<.3);assert.ok(Math.abs(back[2]+.7)<.11);});
test('extreme repeated loading remains finite and floor contact holds',()=>{const m=new FoamMode();for(let i=0;i<10000;i++){m.step(i%2?.1:.001,i%100<50?1:0,2);assert.ok(Number.isFinite(m.value)&&m.value>=0&&m.value<=1);}const p=deformPoint(0,.03,0,1,[{center:[0,.1,0],normal:[0,1,0],radius:1,strength:1,mode:{value:1}}],[0,0,0]);assert.ok(p[1]>=.025);});
test('Q elastic release jiggles in both directions and settles',()=>{const j=new JellyMode();j.kick(.9);const values=[];for(let i=0;i<240;i++)values.push(j.step(1/60));assert.ok(Math.max(...values)>.25);assert.ok(Math.min(...values)<-.08);assert.ok(Math.abs(j.value)<.001);});
test('Q elastic motion is frame-rate independent',()=>{const values=[30,60,120].map(hz=>{const j=new JellyMode();j.kick(.8);for(let i=0;i<hz;i++)j.step(1/hz);return j.value;});assert.ok(Math.max(...values)-Math.min(...values)<1e-10);});

