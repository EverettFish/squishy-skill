// Reduced-order, two-mode viscoelastic foam. Stable exact exponential time stepping.
// This is a perceptual constitutive approximation, not calibrated FEM.
export class FoamMode {
  constructor(){this.fast=0;this.slow=0;this.value=0;}
  step(dt,load,recovery=6){
    dt=Math.max(0,Math.min(dt,.1));load=Math.max(0,Math.min(1,load));
    const tf=load>this.fast?.075:recovery*.055;
    const ts=load>this.slow?.65:recovery/3.4;
    this.fast+=(load-this.fast)*(-Math.expm1(-dt/tf));
    this.slow+=(load-this.slow)*(-Math.expm1(-dt/ts));
    this.value=.3*this.fast+.7*this.slow;
    if(this.value<.0001&&load===0)this.reset();
    return this.value;
  }
  reset(){this.fast=this.slow=this.value=0;}
}
// An elastic skin mode sits on top of slow foam memory: a brief, damped jiggle.
export class JellyMode {
  constructor(){this.value=0;this.velocity=0;}
  kick(strength){this.velocity=Math.min(8,this.velocity+Math.max(0,strength)*8);}
  step(dt){
    dt=Math.max(0,Math.min(dt,.1));const w=13,zeta=.24,a=w*zeta,b=w*Math.sqrt(1-zeta*zeta);
    const x=this.value,v=this.velocity,e=Math.exp(-a*dt),c=Math.cos(b*dt),s=Math.sin(b*dt);
    this.value=e*(x*c+(v+a*x)*s/b);
    this.velocity=e*(v*c-(a*v+w*w*x)*s/b);
    if(Math.abs(this.value)<.0001&&Math.abs(this.velocity)<.001){this.value=0;this.velocity=0;}
    return this.value;
  }
}
export function squashFactors(amount){
  const vertical=1-.48*amount;
  // Compressible foam: air is expelled, so volume decreases rather than staying liquid-like.
  const lateral=1+.235*amount;
  return [lateral,vertical,lateral];
}
export function deformPoint(x,y,z,amount,dents,out,jiggle=0){
  let px=x,py=y,pz=z;
  for(const d of dents){
    const a=d.mode.value*d.strength;if(a<.0001)continue;
    const dx=x-d.center[0],dy=y-d.center[1],dz=z-d.center[2];
    const along=dx*d.normal[0]+dy*d.normal[1]+dz*d.normal[2];
    const rx=dx-along*d.normal[0],ry=dy-along*d.normal[1],rz=dz-along*d.normal[2];
    const r2=(rx*rx+ry*ry+rz*rz)/(d.radius*d.radius);
    const depth=Math.exp(-r2*2.1)*Math.exp(-along*along/1.25)*a*.48;
    const rim=Math.exp(-r2*1.1)*a*.16;
    px+=-d.normal[0]*depth+rx*rim;
    py+=-d.normal[1]*depth+ry*rim;
    pz+=-d.normal[2]*depth+rz*rim;
  }
  const f=squashFactors(amount);
  out[0]=px*f[0]*(1-.14*jiggle);out[1]=Math.max(.025,py*f[1]*(1+.22*jiggle));out[2]=pz*f[2]*(1-.14*jiggle);
  return out;
}
