#!/usr/bin/env python3
"""Package the exact validated firmware and instructions for the official updater."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_polymega_toggle import CANDIDATE_NAME


def package(source, output):
    data = source.read_bytes()
    manifest = json.loads((ROOT/'firmware/start-right-toggle/patch_manifest.json').read_text())
    if len(data) != manifest['bytes'] or hashlib.sha256(data).hexdigest() != manifest['candidate_sha256']:
        raise ValueError('Firmware does not match the validated candidate')
    files = {
        CANDIDATE_NAME: data,
        'README.txt': (ROOT/'release/README.txt').read_text().replace('\n', '\r\n').encode('utf-8'),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, contents)
    print(f'{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', type=Path, required=True, help='Validated custom .bxw file')
    parser.add_argument('--output', type=Path, required=True, help='New firmware ZIP path')
    args = parser.parse_args()
    package(args.firmware, args.output)
