#!/usr/bin/env python3
"""Create a self-contained squishy viewer; no framework or npm install required."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import urllib.request

THREE_VERSION='0.180.0'
FILES={'build/three.module.js':'three.module.js','build/three.core.js':'three.core.js','examples/jsm/loaders/GLTFLoader.js':'addons/loaders/GLTFLoader.js','examples/jsm/controls/OrbitControls.js':'addons/controls/OrbitControls.js','examples/jsm/environments/RoomEnvironment.js':'addons/environments/RoomEnvironment.js','examples/jsm/utils/BufferGeometryUtils.js':'addons/utils/BufferGeometryUtils.js','LICENSE':'THREE-LICENSE.txt'}

def three_vendor(target):
    with urllib.request.urlopen('https://registry.npmjs.org/three/'+THREE_VERSION,timeout=60) as r: meta=json.load(r)
    url=meta['dist']['tarball']
    if not url.startswith('https://registry.npmjs.org/three/-/'): raise RuntimeError('Unexpected package download origin')
    with urllib.request.urlopen(url,timeout=90) as r: blob=r.read()
    integrity=meta['dist']['integrity'];algorithm,expected=integrity.split('-',1)
    if algorithm!='sha512' or base64.b64encode(hashlib.sha512(blob).digest()).decode()!=expected: raise RuntimeError('Three.js package integrity mismatch')
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
        for source,name in FILES.items():
            data=t.extractfile('package/'+source)
            if data is None: raise RuntimeError('Missing Three.js dependency: '+source)
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data.read())

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--name',default='小捏捏');p.add_argument('--lang',choices=['zh','en'],default='zh');p.add_argument('--vendor-from',type=Path,help='Reuse an existing complete viewer vendor directory');args=p.parse_args()
    root=args.output.resolve();web=root/'web'
    if web.exists() and any(web.iterdir()): p.error('web/ already contains files; refusing to overwrite')
    source=Path(__file__).resolve().parents[1]/'assets'/'web'
    shutil.copytree(source,web,dirs_exist_ok=True);(web/'assets').mkdir(exist_ok=True)
    (web/'toy.json').write_text(json.dumps({'name':args.name,'model':'./assets/toy.glb','language':args.lang},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.vendor_from:
        for name in FILES.values():
            original=args.vendor_from/name
            if not original.is_file():p.error('Vendor directory missing '+name)
        shutil.copytree(args.vendor_from,web/'vendor',dirs_exist_ok=True)
    else: three_vendor(web/'vendor')
    for d in ['blender','references','renders']:(root/d).mkdir(exist_ok=True)
    shutil.copy2(Path(__file__).with_name('serve.py'),root/'serve.py')
    print(json.dumps({'project':str(root),'web':str(web),'next':'Add web/assets/toy.glb, then run python serve.py web'},ensure_ascii=False))

if __name__=='__main__':main()
