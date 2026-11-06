"""Public package identity; the development probe keeps its separate identity."""
import json

VERSION = '0.0.8'
MOD_ID = 'com.github.YangtzeMa.Vic-mod'


def configure(output):
    path = output / '.metadata/metadata.json'
    data = json.loads(path.read_text('utf-8'))
    data.update(name='Vicmod Achievement Memory', id=MOD_ID, version=VERSION,
                picture='thumbnail.png',
                short_description='Local achievement memory. Run the companion helper for persistence.')
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
