"""Derive a closed volumetric mesh and projective UVs; leave source bitmaps unchanged."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
im=np.asarray(Image.open(ROOT/'references/faithful/front.png').convert('RGB'))/255
h,w=im.shape[:2];yy,xx=np.mgrid[:h,:w]
mask=((im.max(2)-im.min(2)>.085)|(im.min(2)<.72))&(yy>=104)&(yy<1118)
shoe=((yy>1040)&(yy<1118)&(((xx>319)&(xx<446))|((xx>466)&(xx<591))))
mask|=shoe&(im.min(2)<.93)
shoe_shape=Image.new('1',(w,h));draw=ImageDraw.Draw(shoe_shape)
draw.polygon([(334,1040),(365,1033),(404,1039),(424,1057),(440,1089),(442,1104),(434,1111),(408,1116),(350,1116),(328,1110),(323,1092),(327,1065)],fill=1)
draw.polygon([(499,1031),(543,1034),(559,1045),(569,1068),(582,1086),(586,1105),(579,1114),(548,1118),(497,1114),(475,1103),(474,1088),(486,1052)],fill=1)
mask[yy>1040]&=np.asarray(shoe_shape)[yy>1040]
labels,n=ndi.label(mask);sizes=np.bincount(labels.ravel());sizes[0]=0;mask=ndi.binary_fill_holes(labels==sizes.argmax())
mask=ndi.binary_closing(mask,iterations=1)
distance=ndi.distance_transform_edt(mask)
# A 3-pixel sampling gives fine silhouette detail without a billboard.
step=2;xs=np.arange(0,w,step);ys=np.arange(0,h,step);grid=-np.ones((len(ys),len(xs)),dtype=np.int32)
coords=[]
for j,y in enumerate(ys):
 for i,x in enumerate(xs):
  if mask[y,x]:grid[j,i]=len(coords);coords.append((x,y))
coords=np.array(coords);faces=[]
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  a,b,c,d=grid[j,i],grid[j,i+1],grid[j+1,i+1],grid[j+1,i]
  for tri in [(a,b,c),(a,c,d)]:
   if min(tri)>=0:faces.append(tri)
faces=np.array(faces,dtype=np.int32)
edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
unique,count=np.unique(edges,axis=0,return_counts=True);boundary=unique[count==1];boundaryverts=np.unique(boundary)
x,y=coords.T;d=distance[y,x];depth=d*.70
# Front/back volumes are inferred, anchored to actual reference landmarks.
for cx,cy,rx,rz,ry in [(469,290,188,182,145),(469,205,169,110,135),(465,350,165,123,138),(471,602,141,157,99),(294,538,90,95,57),(588,607,61,137,53),(245,450,47,58,34),(602,755,31,60,24),(393,879,53,122,48),(520,879,53,122,48),(392,988,51,75,47),(521,988,51,75,47),(378,1080,64,43,82),(525,1080,65,44,82)]:
 q=((x-cx)/rx)**2+((y-cy)/rz)**2;dep=ry*np.sqrt(np.maximum(0,1-q));depth=np.maximum(depth,dep)
depth*=np.minimum(1,np.sqrt(d/14))
depth+=18*np.exp(-((x-466)/21)**2-((y-350)/19)**2)
depth[boundaryverts]=0
scale=4.1/(1117-107)
front=np.column_stack(((x-465)*scale,-depth*scale,(1117-y)*scale))
back=front.copy();back[:,1]=depth*.86*scale
points=np.concatenate([front,back]);N=len(front)
# Front winding faces -Y; back faces +Y.
fullfaces=np.concatenate([faces[:,::-1],faces+N]);materials=np.concatenate([np.zeros(len(faces),dtype=np.int32),np.ones(len(faces),dtype=np.int32)])
side=[]
for a,b in boundary:side.extend([(a,b,b+N),(a,b+N,a+N)])
# Boundary is coincident; welding in Blender closes the shell.
fullfaces=np.concatenate([fullfaces,np.array(side)]);materials=np.concatenate([materials,np.ones(len(side),dtype=np.int32)])
uvfront=np.column_stack((x/(w-1),1-y/(h-1)))
sheet=np.asarray(Image.open(ROOT/'references/faithful/turnaround.png').convert('RGB'))/255
sh,sw=sheet.shape[:2];backmask=(sheet.max(2)-sheet.min(2)>.10)|(sheet.min(2)<.72);backmask[:,:1000]=False;backmask=ndi.binary_erosion(backmask,iterations=4)
# Avoid projecting white background onto silhouette edges of the inferred rear.
_,nearest=ndi.distance_transform_edt(~backmask,return_indices=True)
by=np.interp(y,[107,270,454,732,820,932,1117],[38,195,330,581,653,767,952])
bx=1219-(x-465)*.88
bi=np.clip(np.rint(bx).astype(int),1001,sw-1);bj=np.clip(np.rint(by).astype(int),0,sh-1)
bad=~backmask[bj,bi];nearest_x=nearest[1,bj[bad],bi[bad]].copy();nearest_y=nearest[0,bj[bad],bi[bad]].copy();bi[bad]=nearest_x;bj[bad]=nearest_y
uvback=np.column_stack((bi/(sw-1),1-bj/(sh-1)))
side_mask=(sheet.max(2)-sheet.min(2)>.1)|(sheet.min(2)<.72);side_mask[:,:520]=False;side_mask[:,1000:]=False;side_mask=ndi.binary_erosion(side_mask,iterations=4)
_,sn=ndi.distance_transform_edt(~side_mask,return_indices=True)
sx=np.clip(np.rint(790+points[:,1]/scale*.90).astype(int),521,999)
sy=np.clip(np.rint(np.tile(np.interp(y,[107,270,454,732,820,932,1117],[38,190,338,581,657,774,952]),2)).astype(int),0,sh-1)
bad=~side_mask[sy,sx];nx=sn[1,sy[bad],sx[bad]].copy();ny=sn[0,sy[bad],sx[bad]].copy();sx[bad]=nx;sy[bad]=ny
uvside=np.column_stack((sx/(sw-1),1-sy/(sh-1)))
np.savez_compressed(ROOT/'blender/reference-mesh.npz',vertices=points,faces=fullfaces,materials=materials,uvfront=np.concatenate([uvfront,uvfront]),uvback=np.concatenate([uvback,uvback]),uvside=uvside)
print('Reference geometry:',len(points),'vertices',len(fullfaces),'triangles; original textures unchanged')
