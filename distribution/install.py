"""Prepare recipient-specific mod files and a non-destructive Documents junction."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'companion'), str(ROOT / 'scripts')]
from build_memory_ui import build
from memory import read_records
from release_metadata import configure, MOD_ID, VERSION


def validate_game(path):
    path = Path(path).expanduser().resolve()
    if (path / 'game/common/achievements').is_dir():
        path /= 'game'
    if not (path / 'common/achievements').is_dir():
        raise ValueError('Choose the Victoria 3 install folder or its game subfolder')
    version = json.loads((path.parent / 'launcher/launcher-settings.json').read_text('utf-8-sig'))['rawVersion']
    if not version.startswith('1.15.'):
        raise ValueError(f'Unsupported game build {version}; this package targets 1.15.x')
    return path


def detect_game():
    if os.name != 'nt':
        return None
    import winreg
    roots = []
    for hive, key, value in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                             (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')]:
        try:
            with winreg.OpenKey(hive, key) as handle:
                roots.append(Path(winreg.QueryValueEx(handle, value)[0]))
        except OSError:
            pass
    libraries = list(roots)
    for root in roots:
        file = root / 'steamapps/libraryfolders.vdf'
        if file.is_file():
            libraries.extend(Path(value.replace('\\\\', '\\')) for value in
                             re.findall(r'"path"\s*"([^"\r\n]+)"', file.read_text('utf-8-sig')))
    for library in libraries:
        candidate = library / 'steamapps/common/Victoria 3/game'
        if (candidate / 'common/achievements').is_dir():
            return validate_game(candidate)
    return None


def prepare(game, user, root=ROOT, link=True):
    if (root / '.git').exists():
        raise ValueError('Install from an extracted release ZIP, not the development checkout')
    game = validate_game(game)
    output = root / 'mod'
    destination = user / 'mod/vicmod_achievement_memory'
    if os.path.lexists(destination) and not (destination.is_junction() and destination.resolve() == output.resolve()):
        raise ValueError(f'Refusing to replace another directory or link: {destination}')
    metadata = output / '.metadata/metadata.json'
    if output.exists() and (not metadata.is_file() or json.loads(metadata.read_text('utf-8'))['id'] not in {MOD_ID, MOD_ID + '.capture-probe'}):
        raise ValueError('The output mod directory is not owned by this package')
    state = read_records(user / 'vicmod_achievement_memory/records.json')
    result = build(game, output, state['completed'], public=True)
    configure(output)
    if link and not os.path.lexists(destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(VICMOD_LINK_PATH=str(destination), VICMOD_TARGET_PATH=str(output.resolve()))
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                        "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:VICMOD_LINK_PATH -Value $env:VICMOD_TARGET_PATH | Out-Null"],
                       env=env, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if link and (not destination.is_junction() or destination.resolve() != output.resolve()):
        raise ValueError('Junction verification failed')
    config = root / '.local/release-config.json'
    config.parent.mkdir(exist_ok=True)
    config.write_text(json.dumps({'game': str(game), 'user': str(user.resolve()), 'version': VERSION}, indent=2), encoding='utf-8')
    return result


def main():
    if sys.version_info < (3, 12) or os.name != 'nt':
        raise SystemExit('Requires Windows and Python 3.12 or later')
    from run_memory import documents, GameProcess
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path)
    args = parser.parse_args()
    if GameProcess().find():
        raise SystemExit('Close Victoria 3 before installing')
    game = args.game or detect_game()
    if game is None:
        game = Path(input('Victoria 3 install folder (paste path): ').strip().strip('"'))
    print('Prepared:', prepare(game, documents() / 'Paradox Interactive/Victoria 3'))
    print('Restart Paradox Launcher. Add Vicmod Achievement Memory to a playset using the Launcher UI.')
    print('Before each gaming session, run START.cmd and wait for MEMORY_READY. Keep this folder in place.')


if __name__ == '__main__':
    main()
