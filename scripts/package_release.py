"""Build a deterministic source-installer ZIP from an explicit public allowlist."""
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'companion'))
from release_metadata import VERSION, MOD_ID

FILES = {
    **{f'companion/{name}.py': f'companion/{name}.py' for name in ['identity', 'memory', 'run_memory', 'release_metadata']},
    **{f'scripts/{name}.py': f'scripts/{name}.py' for name in ['build_identity_probe', 'build_memory_ui', 'memory_controls']},
    'distribution/install.py': 'distribution/install.py',
    'distribution/start.py': 'distribution/start.py',
    'INSTALL.cmd': 'distribution/INSTALL.cmd',
    'START.cmd': 'distribution/START.cmd',
    'README_zh_CN.md': 'distribution/README_release.md',
    'mod/thumbnail.png': 'mod/thumbnail.png',
    'mod/.metadata/thumbnail.png': 'mod/.metadata/thumbnail.png',
}


def package(root=ROOT, destination=None):
    destination = destination or root / 'dist'
    destination.mkdir(parents=True, exist_ok=True)
    prefix = f'vicmod-achievement-memory-{VERSION}'
    output = destination / f'{prefix}-windows-source.zip'
    payload = {name: (root / source).read_bytes() for name, source in FILES.items()}
    metadata = json.loads((root / 'mod/.metadata/metadata.json').read_text('utf-8'))
    metadata.update(id=MOD_ID, name='Vicmod Achievement Memory', version=VERSION,
                    short_description='Run INSTALL.cmd before enabling this local achievement memory mod.')
    payload['mod/.metadata/metadata.json'] = json.dumps(metadata, indent=2).encode('utf-8')
    payload['VERSION.txt'] = (VERSION + '\nWindows source installer; Python >=3.12; Victoria 3 1.15.x\n').encode('ascii')
    manifest = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(payload.items()))
    payload['MANIFEST.sha256'] = manifest.encode('ascii')
    with ZipFile(output, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = ZipInfo(prefix + '/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    with ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(payload):
            raise ValueError('Release archive validation failed')
        for name, data in payload.items():
            if archive.read(prefix + '/' + name) != data:
                raise ValueError('Release bytes differ: ' + name)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n', encoding='ascii')
    print(f'PASS: {output.name}, {output.stat().st_size} bytes, {len(payload)} files; SHA256 {digest}')
    return output


if __name__ == '__main__':
    package()
