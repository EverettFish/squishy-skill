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

// Local gel v2: independent 3D grab patches, no whole-object scaling.
// Fast elastic skin + slowly relaxing viscous memory, integrated analytically.
export class GelContact {
  constructor(center,normal,radius=1.2){
    this.center=[...center];this.normal=[...normal];this.radius=radius;
    this.target=[0,0,0];this.position=[0,0,0];this.velocity=[0,0,0];this.memory=[0,0,0];
    this.displacement=[0,0,0];this.active=true;this.age=0;this.energy=0;
  }
  setTarget(vector){const length=Math.hypot(...vector),limit=2.25;const scale=length>limit?limit/length:1;for(let i=0;i<3;i++)this.target[i]=vector[i]*scale;}
  release(){this.active=false;this.target.fill(0);}
  step(dt,recovery=5){
    dt=Math.max(0,Math.min(dt,.1));this.age+=dt;
    const w=this.active?24:12,zeta=this.active?.68:.19,a=w*zeta,b=w*Math.sqrt(1-zeta*zeta),e=Math.exp(-a*dt),c=Math.cos(b*dt),s=Math.sin(b*dt);
    this.energy=0;
    for(let i=0;i<3;i++){
      const target=this.active?this.target[i]*.82:0;
      const x=this.position[i]-target,v=this.velocity[i];
      this.position[i]=target+e*(x*c+(v+a*x)*s/b);
      this.velocity[i]=e*(v*c-(a*v+w*w*x)*s/b);
      const mt=this.active?this.target[i]*.18:0,tau=this.active?.5:Math.max(.3,recovery/3.4);
      this.memory[i]+=(mt-this.memory[i])*(-Math.expm1(-dt/tau));
      this.displacement[i]=this.position[i]+this.memory[i];
      this.energy+=Math.abs(this.displacement[i])+Math.abs(this.velocity[i])*.05;
    }
    if(!this.active&&this.energy<.0002){this.position.fill(0);this.velocity.fill(0);this.memory.fill(0);this.displacement.fill(0);this.energy=0;}
    return this.displacement;
  }
}

// A compact C2-continuous support makes distant vertices EXACTLY unchanged.
// Cache these kernels once per contact, instead of distance tests every frame.
export function contactKernel(rest,contact){
  const weights=new Float32Array(rest.length/3),rim=new Float32Array(rest.length);
  const [cx,cy,cz]=contact.center,[nx,ny,nz]=contact.normal,r2=contact.radius**2;
  for(let i=0,j=0;i<rest.length;i+=3,j++){
    const dx=rest[i]-cx,dy=rest[i+1]-cy,dz=rest[i+2]-cz,q=(dx*dx+dy*dy+dz*dz)/r2;
    if(q>=1)continue;const t=1-q,w=t*t*t;weights[j]=w;
    const along=dx*nx+dy*ny+dz*nz;
    rim[i]=(dx-along*nx)*w*.35/contact.radius;
    rim[i+1]=(dy-along*ny)*w*.35/contact.radius;
    rim[i+2]=(dz-along*nz)*w*.35/contact.radius;
  }
  return {contact,weights,rim};
}

export function applyGel(rest,out,kernels){
  out.set(rest);
  for(const {contact:c,weights:w,rim} of kernels){
    if(!c.energy)continue;const d=c.displacement,compression=Math.max(0,-(d[0]*c.normal[0]+d[1]*c.normal[1]+d[2]*c.normal[2]));
    for(let i=0,j=0;i<out.length;i+=3,j++){
      if(w[j]===0)continue;
      out[i]+=d[0]*w[j]+rim[i]*compression;
      out[i+1]+=d[1]*w[j]+rim[i+1]*compression;
      out[i+2]+=d[2]*w[j]+rim[i+2]*compression;
    }
  }
  for(let i=1;i<out.length;i+=3)out[i]=Math.max(.015,out[i]);
  return out;
}
