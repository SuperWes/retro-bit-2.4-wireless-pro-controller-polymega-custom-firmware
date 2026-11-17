#!/usr/bin/env python3
"""Package the Windows installer without any vendor firmware, updater, or PDF."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_polymega_toggle as firmware


def package(output):
    code, _, labels = firmware.extension()
    table = json.dumps([{'offset': o, 'before': b.hex(), 'after': a.hex()}
                        for o, b, a, _ in firmware.patch_regions(code, labels)], indent=2)
    script = (ROOT/'installer/Install.ps1').read_text()
    assert script.count('@@PATCH_TABLE_JSON@@') == 1
    script = script.replace('@@PATCH_TABLE_JSON@@', table)
    files = {name: (ROOT/'installer'/name).read_text() for name in ['Install.cmd', 'README.txt']}
    files['Install.ps1'] = script
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, contents.replace('\n', '\r\n').encode('utf-8'))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f'{digest}  {output.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New installer ZIP path')
    package(parser.parse_args().output)
