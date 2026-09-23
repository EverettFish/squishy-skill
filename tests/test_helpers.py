import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SPEC=importlib.util.spec_from_file_location('setup',Path(__file__).resolve().parents[1]/'scripts'/'ensure_blender.py')
setup=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(setup)

class SetupTests(unittest.TestCase):
    def test_architectures(self):
        self.assertEqual(setup.platform_suffix('Windows','AMD64'),'windows-x64.zip')
        self.assertEqual(setup.platform_suffix('Windows','ARM64'),'windows-arm64.zip')
        self.assertEqual(setup.platform_suffix('Darwin','arm64'),'macos-arm64.dmg')
        with self.assertRaises(RuntimeError):setup.platform_suffix('Linux','armv7')
    def test_latest_semantic_version(self):
        index='<a href="blender-4.5.9-windows-x64.zip">x</a><a href="blender-4.5.14-windows-x64.zip">x</a>'
        self.assertEqual(setup.select_release(index,'windows-x64.zip')[1],'4.5.14')
    def test_checksum_missing_fails_closed(self):
        with self.assertRaises(RuntimeError):setup.manifest_hash('a'*64+'  another.zip','blender.zip')
        self.assertEqual(setup.manifest_hash('a'*64+' *blender.zip','blender.zip'),'a'*64)
    def test_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ['../outside','C:/evil','/absolute','..\\escape']:
                with self.assertRaises(RuntimeError):setup.safe_member(Path(d),name)
    def test_zip_extract_and_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);z=root/'good.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('blender/readme.txt','ok')
            setup.extract(z,root/'out');self.assertEqual((root/'out/blender/readme.txt').read_text(),'ok')
            with zipfile.ZipFile(root/'bad.zip','w') as f:f.writestr('../escape.txt','no')
            with self.assertRaises(RuntimeError):setup.extract(root/'bad.zip',root/'out2')

if __name__=='__main__':unittest.main()
