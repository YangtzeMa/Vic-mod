"""Keep local achievement memory across game exits. No OCR or process memory access."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import re
import sys
import time

from identity import PREFIX, BULK_PREFIX, read_order
from memory import remember_clicks

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_memory_ui import build


def click_lines(logs):
    def rotation(path):
        match = re.fullmatch(r'debug\.(\d+)\.log', path.name)
        return int(match.group(1)) + 1 if match else 0
    files = [p for p in logs.glob('debug*.log') if re.fullmatch(r'debug(?:\.\d+)?\.log', p.name)]
    for path in sorted(files, key=rotation, reverse=True):
        try:
            for line in path.read_text('utf-8-sig', errors='replace').splitlines():
                if PREFIX in line or BULK_PREFIX in line:
                    yield line
        except (FileNotFoundError, PermissionError):
            continue


def synchronize(game, user, output, release=False):
    records = user / 'vicmod_achievement_memory/records.json'
    data, report = remember_clicks(records, click_lines(user / 'logs'), read_order(game))
    result = build(game, output, data['completed'], public=release)
    if release:
        from release_metadata import configure
        configure(output)
    return dict(result, added=report['added'], rejected=report['rejected'])


class GameProcess:
    """Find the game while idle, then wait on its exit handle without polling."""
    def __init__(self):
        if sys.platform != 'win32':
            raise OSError('The background helper requires Windows')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        class Entry(ctypes.Structure):
            _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                        ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                        ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                        ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                        ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]
        self.Entry = Entry
        self.kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        for name in ['Process32FirstW', 'Process32NextW']:
            method = getattr(self.kernel, name)
            method.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
            method.restype = wintypes.BOOL
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL

    def find(self):
        snapshot = self.kernel.CreateToolhelp32Snapshot(2, 0)
        if snapshot == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = self.Entry()
            entry.dwSize = ctypes.sizeof(entry)
            more = self.kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while more:
                if entry.szExeFile.lower() == 'victoria3.exe':
                    return entry.th32ProcessID
                more = self.kernel.Process32NextW(snapshot, ctypes.byref(entry))
            return None
        finally:
            self.kernel.CloseHandle(snapshot)

    def wait(self, pid):
        # SYNCHRONIZE only; no game memory, injection, debug or cheat capability.
        handle = self.kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            if self.find() != pid:
                return
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if self.kernel.WaitForSingleObject(handle, 0xFFFFFFFF) != 0:
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(handle)


def documents():
    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer):
        raise OSError('Cannot locate Windows Documents')
    return Path(buffer.value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--user', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '.local/memory-probe')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--release', action='store_true', help='Keep the stable public mod identity')
    args = parser.parse_args()
    process = GameProcess()
    user = args.user or documents() / 'Paradox Interactive/Victoria 3'
    directory = user / 'vicmod_achievement_memory'
    directory.mkdir(parents=True, exist_ok=True)
    import msvcrt
    with (directory / 'helper.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit('Local memory helper is already running')
        if args.once and process.find():
            raise SystemExit('Exit the game before rebuilding the memory snapshot')
        while True:
            pid = process.find()
            if pid:
                print(f'Waiting for game process {pid} to exit.', flush=True)
                process.wait(pid)
                # The closed process has released its log files. Do not rebuild
                # if a new instance was already launched in the meantime.
                if process.find():
                    continue
            report = synchronize(args.game, user, args.output, release=args.release)
            print('MEMORY_READY ' + json.dumps(report, ensure_ascii=False), flush=True)
            if args.once:
                return
            while not process.find():
                # Only enumerate process names while the game is absent.
                # While playing, the wait above blocks without CPU polling.
                time.sleep(2)


if __name__ == '__main__':
    main()
