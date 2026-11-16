#!/usr/bin/env python3
"""Create an offline C/Z-swap candidate from the exact official USB Pro 1.1 image.

No device access or flashing. Refuses other firmware/updater versions.
USE AT YOUR OWN RISK: flashing the experimental output can permanently brick
the V2 USB receiver. No hardware validation, warranty, or recovery guarantee.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

STOCK_SHA = '12c69fc5ebd2e76e40394428960548b79fe44e5a69d728691a8ad52b478bd55a'
UPDATER_SHA = '27f11a4bb3becc5426025025fe376d45f9b6da54f41a347750466f069592b4d7'
DECODED_SHA = '996a4eaed2ea0fd570b4960e6a1d85d15f0a0f1e747d63173e3e179d0158df76'
SOURCE_URL = 'https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip'
PATCHES = [
    (0x2489, 0xe0, 0xe2, 'PS3 L1/pressure block: test source bit 18 instead of 16'),
    (0x249d, 0xe2, 0xe0, 'PS3 R1/pressure block: test source bit 16 instead of 18'),
    (0x5890, 0x08, 0x09, 'XInput C/L source: emit RB instead of LB'),
    (0x5892, 0x09, 0x08, 'XInput Z/R source: emit LB instead of RB'),
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def check(condition, message='Firmware consistency check failed'):
    if not condition:
        raise ValueError(message)

def write_new(path, data):
    with path.open('xb') as f:
        f.write(data)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stock', type=Path, required=True)
    ap.add_argument('--updater', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    stock, updater = args.stock.read_bytes(), args.updater.read_bytes()
    check(len(stock) == 32768 and digest(stock) == STOCK_SHA, 'Wrong stock firmware')
    check(digest(updater) == UPDATER_SHA, 'Wrong updater executable')
    encode = updater[0x4124:0x4224]
    check(len(encode) == 256 and len(set(encode)) == 256)
    decode = bytes(encode.index(i) for i in range(256))
    original = stock.translate(decode)
    check(digest(original) == DECODED_SHA)
    check(original.translate(encode) == stock, 'Stock round trip failed')
    check(original[0x2488:0x248b] == bytes.fromhex('30 e0 0d'))
    check(original[0x249c:0x249f] == bytes.fromhex('30 e2 0d'))
    check(original[0x588f:0x5893] == bytes.fromhex('10 08 12 09'))
    modified = bytearray(original)
    for offset, before, after, _ in PATCHES:
        check(modified[offset] == before)
        modified[offset] = after
    modified = bytes(modified)
    encoded = modified.translate(encode)
    check(encoded.translate(decode) == modified)
    expected = [p[0] for p in PATCHES]
    check([i for i, (a, b) in enumerate(zip(original, modified)) if a != b] == expected)
    check([i for i, (a, b) in enumerate(zip(stock, encoded)) if a != b] == expected)
    check(Counter(original) == Counter(modified))
    check(Counter(stock) == Counter(encoded))
    check(original[:0x1000] == modified[:0x1000])
    check(original[0x7fc0:] == modified[0x7fc0:])
    for offset in range(0, len(stock), 32):
        check(sum(original[offset:offset+32]) == sum(modified[offset:offset+32]))
        check(sum(stock[offset:offset+32]) == sum(encoded[offset:offset+32]))
    manifest = {
        'risk_notice': 'USE_AT_YOUR_OWN_RISK.txt',
        'status': 'EXPERIMENTAL; no hardware validation or flashing performed',
        'target': 'Retro-Bit V2 USB receiver for Saturn Pro; NOT controller or Saturn-port receiver',
        'base_filename': args.stock.name,
        'base_source_url': SOURCE_URL,
        'base_sha256': STOCK_SHA,
        'updater_sha256': UPDATER_SHA,
        'decoded_base_sha256': DECODED_SHA,
        'candidate_sha256': digest(encoded),
        'decoded_candidate_sha256': digest(modified),
        'bytes': len(encoded),
        'changes': [{'offset': f'0x{o:04x}', 'decoded_before': f'{a:02x}',
                     'decoded_after': f'{b:02x}', 'encoded_before': f'{stock[o]:02x}',
                     'encoded_after': f'{encoded[o]:02x}', 'reason': reason}
                    for o, a, b, reason in PATCHES],
        'scope': 'Swap C/L and Z/R in XInput and PS3 compatibility output profiles only.',
        'unchanged': ['ZL/ZR', 'A/B/X/Y', 'D-pad', 'analog axes', 'stick clicks',
                      'Start/Select/Home', 'Switch and D-input profiles',
                      'USB descriptors', 'pairing logic', 'update metadata'],
        'structural_checks': ['Exact input hashes', 'Stock decode/encode round trip',
                              'Candidate decode/encode round trip', 'Exactly four changed bytes',
                              'Same size', 'Boot-region and device metadata unchanged',
                              'Identical encoded and decoded 32-byte-block additive sums'],
    }
    notice = Path(__file__).with_name('USE_AT_YOUR_OWN_RISK.txt').read_bytes()
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output/'USE_AT_YOUR_OWN_RISK.txt', notice)
    write_new(args.output/'retrobit_usb_pro_1.1_polymega_cz_swap_EXPERIMENTAL.bxw', encoded)
    write_new(args.output/'stock_usb_pro_1.1.bxw', stock)
    write_new(args.output/'stock_decoded.bin', original)
    write_new(args.output/'candidate_decoded.bin', modified)
    write_new(args.output/'patch_manifest.json', (json.dumps(manifest, indent=2)+'\n').encode())
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
