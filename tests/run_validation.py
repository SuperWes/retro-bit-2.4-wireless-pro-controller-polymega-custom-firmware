#!/usr/bin/env python3
"""Build and validate the toggle offline, optionally saving a reviewed package."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_polymega_toggle as firmware


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args, success=True):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, check=False)
    if success and result.returncode != 0:
        raise RuntimeError(f'Command failed: {result.args}\n{result.stdout}{result.stderr}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True, help='Official firmware obtained from Retro-Bit')
    parser.add_argument('--updater', type=Path, required=True)
    parser.add_argument('--cxx', default='c++')
    parser.add_argument('--output', type=Path, help='New package directory; must not exist')
    args = parser.parse_args()
    updater = args.updater.resolve()
    if args.output is not None and args.output.exists():
        raise ValueError('Output directory already exists')
    with tempfile.TemporaryDirectory(prefix='retrobit-polymega-validate-') as temporary:
        work = Path(temporary)
        generated = work/'generated'
        builder = ROOT/'build_polymega_toggle.py'
        stock = args.stock.resolve()
        command(sys.executable, builder, '--stock', stock, '--updater', updater, '--output', generated)
        original = (generated/'stock_decoded.bin').read_bytes()
        candidate = (generated/'candidate_decoded.bin').read_bytes()
        encoded = (generated/firmware.CANDIDATE_NAME).read_bytes()
        # Rebuild through the library entry point and compare every emitted byte.
        rebuilt = firmware.build(stock.read_bytes(), updater.read_bytes())
        if (original, candidate, encoded) != rebuilt[:3]:
            raise AssertionError('Rebuild is not byte-identical')
        verifier = work/'verify_polymega_toggle'
        command(args.cxx, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                ROOT/'tests/verify_polymega_toggle.cpp', '-o', verifier)
        run = command(verifier, generated/'stock_decoded.bin', generated/'candidate_decoded.bin')
        validation = json.loads(run.stdout)
        validation['reproducible_build'] = 'Byte-identical CLI/library rebuild'
        validation['candidate_sha256'] = hashlib.sha256(encoded).hexdigest()

        def reject_image(name, data, expected_error):
            image = work/(name+'.bin')
            image.write_bytes(data)
            result = command(verifier, generated/'stock_decoded.bin', image, success=False)
            if result.returncode == 0 or expected_error not in result.stderr:
                raise AssertionError(f'Negative control {name} was not rejected as expected: {result.stderr}')
            return {'name': name, 'rejected_with': result.stderr.strip()}

        controls = [reject_image('unmodified_stock', original, 'Start+Right failed')]
        for name, offset in [('missing_ps3_dispatch_hook',0x34f4), ('missing_xinput_dispatch_hook',0x34fb)]:
            broken = bytearray(candidate)
            broken[offset:offset+3] = original[offset:offset+3]
            controls.append(reject_image(name, broken, 'Macro state did not reach'))
        # Invert the new XInput state test: disabled now swaps and enabled does not.
        _, _, symbols = firmware.extension()
        broken = bytearray(candidate)
        branch = symbols['xinput_report']+7
        if broken[branch] != 0x60:
            raise AssertionError('Unexpected XInput state branch')
        broken[branch] = 0x70
        controls.append(reject_image('inverted_default_mapping', broken, 'Macro state did not reach'))
        # A one-step X-axis shift must be caught even though C/Z still swap.
        broken = bytearray(candidate)
        if broken[0x2f34] != 0x80:
            raise AssertionError('Unexpected stock XInput axis conversion')
        broken[0x2f34] = 0x81
        controls.append(reject_image('corrupted_analog_axis', broken, 'Macro state did not reach'))
        validation['negative_controls'] = controls

        rejected = []
        for name, bad_stock, bad_updater, expected in [
            ('wrong_firmware', bytes([stock.read_bytes()[0]^1])+stock.read_bytes()[1:], updater.read_bytes(), 'Wrong stock firmware'),
            ('wrong_updater', stock.read_bytes(), bytes([updater.read_bytes()[0]^1])+updater.read_bytes()[1:], 'Wrong updater executable'),
        ]:
            source, executable, output = work/(name+'.bxw'), work/(name+'.exe'), work/(name+'-output')
            source.write_bytes(bad_stock); executable.write_bytes(bad_updater)
            result = command(sys.executable, builder, '--stock', source, '--updater', executable,
                             '--output', output, success=False)
            if result.returncode == 0 or output.exists() or expected not in result.stderr:
                raise AssertionError(f'Input guard failed: {name}')
            rejected.append(name)
        validation['rejected_inputs_without_output'] = rejected
        validation['source_sha256'] = {
            name: sha(ROOT/name) for name in [
                'build_polymega_toggle.py', 'build_cz_swap.py', 'tests/emu8051.hpp',
                'tests/verify_polymega_toggle.cpp', 'tests/run_validation.py',
                'USE_AT_YOUR_OWN_RISK.txt',
            ]
        }
        validation['limitations'] = [
            'Report inputs start after stock radio parsing/calibration; those unchanged paths are not emulated.',
            'PS3 template-copy and legacy nonvolatile-save routines are modeled, not hardware-emulated.',
            'No radio, interrupt scheduling, USB host negotiation, bootloader, flash operation, or Polymega emulation.',
            'hardware_tested describes this offline run only; user-reported device tests are recorded in docs/polymega-hardware-results.json.',
        ]
        summary = json.dumps(validation, indent=2)+'\n'
        if args.output is not None:
            args.output.mkdir(parents=True, exist_ok=False)
            files = {}
            for name in [firmware.CANDIDATE_NAME, 'patch_manifest.json', 'polymega_toggle.asm', 'USE_AT_YOUR_OWN_RISK.txt']:
                files[name] = (generated/name).read_bytes()
            files['validation.json'] = summary.encode()
            for name, data in files.items():
                firmware.write_new(args.output/name, data)
            checksums = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(files.items()))
            firmware.write_new(args.output/'SHA256SUMS.txt', checksums.encode())
        print(summary, end='')


if __name__ == '__main__':
    main()
