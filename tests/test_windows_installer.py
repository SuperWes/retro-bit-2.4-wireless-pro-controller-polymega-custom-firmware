#!/usr/bin/env python3
"""Check firmware packaging and the legacy preparer without launching the updater."""
import argparse
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_polymega_toggle as firmware
from build_cz_swap import SOURCE_URL

ARCHIVE_SHA = '69ac4480738d2c5c3929dd92ce89cd1cf91ec204f866a6f830987c40d3dcd6c3'
# The complete expected image fingerprint, independent of the installer template.
FIRMWARE_SHA = '951904f60c5730deaeb92db09039a9c594e2c70e9d8e34b3c14bcbf103dcea54'


def run_installer(script, destination, official=None, expected_error=None):
    args = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', str(script), '-OutputDirectory', str(destination), '-NoLaunch']
    if official is not None:
        args += ['-OfficialZip', str(official)]
    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    if expected_error is None:
        assert result.returncode == 0, output
    else:
        assert result.returncode != 0 and expected_error in ' '.join(output.split()), output
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    version = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
                                      '$PSVersionTable.PSVersion.ToString()'], text=True).strip()
    assert version.startswith('5.1.'), version
    print('Windows PowerShell:', version)
    with tempfile.TemporaryDirectory(prefix='retrobit installer test ') as folder:
        work = Path(folder)
        extracted = work/'extracted installer'
        with zipfile.ZipFile(args.package) as package:
            assert sorted(package.namelist()) == ['Install.cmd', 'Install.ps1', 'README.txt']
            assert package.testzip() is None
            package.extractall(extracted)
        script = extracted/'Install.ps1'
        assert '@@PATCH_TABLE_JSON@@' not in script.read_text()
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
            official_bytes = response.read()
        assert hashlib.sha256(official_bytes).hexdigest() == ARCHIVE_SHA
        official = work/'official.zip'
        official.write_bytes(official_bytes)
        with zipfile.ZipFile(io.BytesIO(official_bytes)) as vendor:
            stock_path = next(n for n in vendor.namelist() if n.endswith('.bxw'))
            prefix = stock_path.rsplit('Firmware/', 1)[0]
            stock = vendor.read(stock_path)
            updater = vendor.read(prefix+'Update Program/BxUsbUpdate.exe')
            reference = firmware.build(stock, updater)[2]
            assert hashlib.sha256(reference).hexdigest() == FIRMWARE_SHA
            vendor_files = {n[len(prefix):]: vendor.read(n) for n in vendor.namelist()
                            if n.startswith(prefix) and not n.endswith('/')
                            and ('/Update Program/' in n or n.endswith('.pdf'))}

        candidate = work/firmware.CANDIDATE_NAME
        candidate.write_bytes(reference)
        packager = [sys.executable, str(ROOT/'tools/package_firmware_release.py'),
                    '--firmware', str(candidate)]
        archives = [work/'firmware-a.zip', work/'firmware-b.zip']
        for archive in archives:
            subprocess.run(packager + ['--output', str(archive)], check=True)
            with zipfile.ZipFile(archive) as packaged:
                assert set(packaged.namelist()) == {firmware.CANDIDATE_NAME, 'README.txt'}
                assert packaged.testzip() is None
                assert packaged.read(firmware.CANDIDATE_NAME) == reference
                assert b'A WINDOWS PC IS REQUIRED' in packaged.read('README.txt')
        assert archives[0].read_bytes() == archives[1].read_bytes()
        before = archives[0].read_bytes()
        refused = subprocess.run(packager + ['--output', str(archives[0])], capture_output=True)
        assert refused.returncode != 0 and archives[0].read_bytes() == before
        candidate.write_bytes(bytes([reference[0] ^ 1]) + reference[1:])
        rejected_zip = work/'wrong-firmware.zip'
        refused = subprocess.run(packager + ['--output', str(rejected_zip)], capture_output=True)
        assert refused.returncode != 0 and not rejected_zip.exists()
        print('Firmware ZIP: exact image, minimal layout, reproducibility, and input/output guards passed')

        for name, source in [('actual download', None), ('local ZIP', official)]:
            destination = work/name
            run_installer(script, destination, source)
            assert (destination/'Firmware'/firmware.CANDIDATE_NAME).read_bytes() == reference
            for path, contents in vendor_files.items():
                assert (destination/path).read_bytes() == contents, path
            expected = set(vendor_files) | {'Firmware/'+firmware.CANDIDATE_NAME, 'README.txt'}
            actual = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
            assert actual == expected, actual
            print(name+': exact firmware, original updater/DLLs/PDF, and expected layout passed')

        wrong = work/'wrong.zip'
        wrong.write_bytes(b'not the supported firmware archive')
        rejected = work/'wrong ZIP output'
        run_installer(script, rejected, wrong, 'does not match the supported version')
        assert not rejected.exists()
        existing = work/'existing output'
        existing.mkdir()
        sentinel = existing/'keep.txt'
        sentinel.write_text('keep this file')
        run_installer(script, existing, wrong, 'Output already exists')
        assert sentinel.read_text() == 'keep this file' and list(existing.iterdir()) == [sentinel]

        corrupt = work/'corrupt.ps1'
        contents = script.read_text()
        assert contents.count('"after": "026000"') == 1
        corrupt.write_text(contents.replace('"after": "026000"', '"after": "026001"'))
        destination = work/'corrupt output'
        run_installer(corrupt, destination, official, 'Patched firmware checksum failed')
        assert not destination.exists()
        assert not list(work.glob('*.tmp-*'))
        print('Wrong ZIP, corrupted patch, and existing output rejected without modification.')
        print('PASS: packaged installer; no updater launch, USB access, or flashing performed.')


if __name__ == '__main__':
    main()
