"""Interactive helper entry point shipped with the source distribution."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    if sys.version_info < (3, 12):
        raise SystemExit('Requires Python 3.12 or later')
    config = ROOT / '.local/release-config.json'
    if not config.is_file():
        raise SystemExit('Run INSTALL.cmd first')
    data = json.loads(config.read_text('utf-8'))
    from install import validate_game
    game = validate_game(data['game'])
    print('Keep this helper window open (you may minimize it). Wait for MEMORY_READY before launching the game.', flush=True)
    raise SystemExit(subprocess.call([sys.executable, '-u', '-X', 'utf8', str(ROOT / 'companion/run_memory.py'),
                    '--game', str(game), '--user', data['user'], '--output', str(ROOT / 'mod'), '--release']))
