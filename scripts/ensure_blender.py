#!/usr/bin/env python3
"""Locate Blender or install an official, checksum-verified portable copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

BASE = 'https://download.blender.org/release/Blender4.5/'
CACHE = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.cache')) / 'squishy' / 'tools'
IGNORE = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'AppData', '$RECYCLE.BIN'}

def run_version(path):
    try:
        r = subprocess.run([str(path), '--version'], capture_output=True, text=True, timeout=20)
        m = re.search(r'Blender (\d+)\.(\d+)(?:\.(\d+))?', r.stdout)
        if r.returncode == 0 and m and tuple(map(int, m.groups(default='0'))) >= (4, 5, 0):
            return {'path': str(Path(path).resolve()), 'version': m.group(0)}
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None

def walk_candidates(root, max_depth=5):
    root = Path(root)
    if not root.is_dir(): return
    for base, dirs, files in os.walk(root):
        depth = len(Path(base).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in IGNORE] if depth < max_depth else []
        for name in ('blender.exe', 'blender', 'Blender'):
            if name in files: yield Path(base) / name

def discover(search_roots=()):
    candidates = [os.environ.get('BLENDER_PATH'), shutil.which('blender')]
    for root, pattern in [(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')), 'Blender Foundation/Blender*/blender.exe'), (Path('/Applications'), 'Blender*.app/Contents/MacOS/Blender'), (Path.home()/'Applications', 'Blender*.app/Contents/MacOS/Blender')]:
        candidates.extend(root.glob(pattern))
    candidates.extend([Path('/usr/bin/blender'), Path('/usr/local/bin/blender'), Path('/snap/bin/blender')])
    candidates.extend(walk_candidates(CACHE))
    seen = set()
    for p in candidates:
        if p and str(p) not in seen:
            seen.add(str(p)); result = run_version(p)
            if result: return result
    for root in search_roots:
        for p in walk_candidates(root):
            result = run_version(p)
            if result: return result
    return None

def platform_suffix(system=None, machine=None):
    system = system or platform.system(); machine = (machine or platform.machine()).lower()
    arch = 'arm64' if machine in ('arm64', 'aarch64') else 'x64' if machine in ('amd64', 'x86_64', 'x64') else None
    if not arch: raise RuntimeError('Unsupported architecture: '+machine)
    if system == 'Windows': return 'windows-'+arch+'.zip'
    if system == 'Darwin': return 'macos-'+arch+'.dmg'
    if system == 'Linux' and arch == 'x64': return 'linux-x64.tar.xz'
    raise RuntimeError('No supported official portable Blender archive for '+system+'/'+machine)

def fetch_text(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'SquishySkill/1.0'}), timeout=60) as r:
        return r.read().decode('utf-8')

def select_release(index, suffix, version=None):
    names = re.findall(r'href="(blender-(4\.5\.\d+)-'+re.escape(suffix)+r')"', index)
    if version: names = [v for v in names if v[1] == version]
    if not names: raise RuntimeError('No official matching Blender archive found')
    return max(names, key=lambda p: tuple(map(int,p[1].split('.'))))

def manifest_hash(manifest, name):
    for line in manifest.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == name and re.fullmatch('[a-fA-F0-9]{64}', parts[0]): return parts[0].lower()
    raise RuntimeError('Official checksum manifest does not contain '+name)

def safe_member(destination, member):
    # Both separators checked even when extracting a Windows archive on another OS.
    cleaned = member.replace('\\','/')
    if cleaned.startswith('/') or re.match(r'^[A-Za-z]:',cleaned): raise RuntimeError('Unsafe absolute archive path')
    target = (destination / cleaned).resolve()
    if not target.is_relative_to(destination.resolve()): raise RuntimeError('Archive path escapes destination')
    return target

def extract(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix == '.zip':
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                safe_member(destination,item.filename)
                if ((item.external_attr >> 16) & 0o170000) == 0o120000: raise RuntimeError('Unexpected archive symlink')
            z.extractall(destination)
    elif archive.name.endswith('.tar.xz'):
        with tarfile.open(archive) as t:
            for item in t.getmembers():
                safe_member(destination,item.name)
                if item.issym(): safe_member(destination, str(Path(item.name).parent / item.linkname))
                if item.islnk(): safe_member(destination,item.linkname)
                if item.isdev(): raise RuntimeError('Unexpected device in archive')
            t.extractall(destination, filter='data')
    else:
        raw = subprocess.check_output(['hdiutil','attach','-readonly','-nobrowse','-plist',str(archive)])
        entities = plistlib.loads(raw).get('system-entities',[])
        mounts = [e['mount-point'] for e in entities if 'mount-point' in e]
        try:
            app = next((p for m in mounts for p in Path(m).glob('*.app')), None)
            if not app: raise RuntimeError('Blender application not found in official disk image')
            target = destination / app.name
            if target.exists(): raise RuntimeError('Refusing to overwrite existing application: '+str(target))
            subprocess.run(['ditto',str(app),str(target)],check=True)
        finally:
            for m in mounts: subprocess.run(['hdiutil','detach',m],check=False,capture_output=True)

def install(version=None, dry_run=False):
    name, version = select_release(fetch_text(BASE), platform_suffix(), version)
    checksum = manifest_hash(fetch_text(BASE+'blender-'+version+'.sha256'), name)
    info = {'version':version,'url':BASE+name,'sha256':checksum,'destination':str(CACHE/version)}
    if dry_run: return info
    downloads = CACHE/'downloads'; downloads.mkdir(parents=True,exist_ok=True)
    archive=downloads/name
    print('Downloading official Blender portable release…',file=sys.stderr)
    digest=hashlib.sha256()
    with urllib.request.urlopen(BASE+name, timeout=90) as source, archive.open('wb') as target:
        while True:
            block=source.read(1024*1024)
            if not block: break
            digest.update(block);target.write(block)
    if digest.hexdigest()!=checksum: raise RuntimeError('Checksum mismatch; archive will not be extracted or executed')
    destination=CACHE/version
    if destination.exists() and any(destination.iterdir()): raise RuntimeError('Install destination is not empty; inspect it instead of overwriting')
    extract(archive,destination)
    result=discover([destination])
    if not result: raise RuntimeError('Blender extracted but could not run; inspect required system libraries')
    return {**result,'installed':True,'sha256':checksum}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--search-root',action='append',default=[]);p.add_argument('--install',action='store_true');p.add_argument('--dry-run',action='store_true');p.add_argument('--version');args=p.parse_args()
    try:
        if args.dry_run: result=install(args.version,True)
        else:
            result=discover(args.search_root)
            if not result and args.install: result=install(args.version)
        if not result: print(json.dumps({'found':False,'next':'Run with --install to obtain an official portable copy'}));return 2
        print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as e: print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr);return 1

if __name__=='__main__': sys.exit(main())
