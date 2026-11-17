#!/usr/bin/env python3
"""Build volatile Street Fighter and SEGA layout shortcuts for the exact USB receiver Pro 1.1 image.

No USB access, flashing, controller patch, or host configuration is performed.
The stock report builders and their analog conversions remain intact.
USE AT YOUR OWN RISK: flashing the unofficial output can permanently brick
the V2 USB receiver. No warranty or recovery guarantee. Hardware reports are recorded separately.
"""
import argparse
import json
from pathlib import Path

from build_cz_swap import STOCK_SHA, UPDATER_SHA, DECODED_SHA, SOURCE_URL
from build_cz_swap import check, digest, write_new

CODE_START = 0x6000
STATE = 0x85FF
CANDIDATE_NAME = 'retrobit_usb_pro_1.1_polymega.bxw'


class Program:
    """Emit a small, auditable 8051 extension with checked label relocations."""

    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.relocations = []
        self.lines = []

    @property
    def pc(self):
        return CODE_START + len(self.code)

    def label(self, name):
        check(name not in self.labels, 'Duplicate label')
        self.labels[name] = self.pc
        self.lines.append((len(self.code), 0, name + ':'))

    def emit(self, text, *data):
        self.lines.append((len(self.code), len(data), '    ' + text))
        self.code.extend(data)

    def address(self, opcode, mnemonic, target):
        if isinstance(target, str):
            self.relocations.append((len(self.code) + 1, 'absolute', target))
            self.emit(f'{mnemonic} {target}', opcode, 0, 0)
        else:
            self.emit(f'{mnemonic} 0x{target:04x}', opcode, target >> 8, target & 255)

    def branch(self, opcode, mnemonic, label, immediate=None):
        prefix = [opcode] if immediate is None else [opcode, immediate]
        self.relocations.append((len(self.code) + len(prefix), 'relative', label))
        operand = '' if immediate is None else f'a,#0x{immediate:02x},'
        self.emit(f'{mnemonic} {operand}{label}', *prefix, 0)

    def finish(self):
        for offset, kind, label in self.relocations:
            target = self.labels[label]
            if kind == 'absolute':
                self.code[offset:offset+2] = target.to_bytes(2, 'big')
            else:
                delta = target - (CODE_START + offset + 1)
                check(-128 <= delta <= 127, 'Relative branch out of range')
                self.code[offset] = delta & 255
        listing = [
            '; Generated from build_polymega_toggle.py; addresses are decoded ROM offsets.',
            '; Stock Start+Right/Up hold detection enters hooks at 0x26b6/0x26e1.',
            '; State 0x85ff is volatile and cleared by the stock 0x8000..0x8fff startup loop.',
            '; Analog axes/triggers use the unchanged stock report builders.',
        ]
        for offset, size, text in self.lines:
            encoded = self.code[offset:offset+size].hex(' ')
            listing.append(f'{CODE_START+offset:04x}  {encoded:<9} {text}')
        return bytes(self.code), '\n'.join(listing) + '\n'


def extension():
    p = Program()
    # Two exclusive presets. Selecting the active one returns to stock; selecting
    # the other replaces it. The stock hold detector handles timing and rearming.
    for name, state, direction, legacy, resume in [
        ('toggle', 1, 0x20, 4, 0x26c1),
        ('toggle_sega', 2, 0x40, 2, 0x26ec),
    ]:
        p.label(name)
        p.address(0x90, 'mov dptr,#', 0x8542)
        p.emit('movx a,@dptr', 0xe0)
        p.branch(0xb4, 'cjne', name+'_check_xinput', 2)
        p.branch(0x80, 'sjmp', name+'_pc')
        p.label(name+'_check_xinput')
        p.branch(0xb4, 'cjne', name+'_legacy', 3)
        p.label(name+'_pc')
        p.address(0x90, 'mov dptr,#', 0x8527)
        p.emit('movx a,@dptr', 0xe0)
        p.emit('anl a,#0xf0', 0x54, 0xf0)
        p.branch(0xb4, 'cjne', name+'_resume', direction)
        p.address(0x90, 'mov dptr,#', STATE)
        p.emit('movx a,@dptr', 0xe0)
        p.branch(0xb4, 'cjne', name+'_select', state)
        p.emit('clr a', 0xe4)
        p.branch(0x80, 'sjmp', name+'_store')
        p.label(name+'_select')
        p.emit(f'mov a,#{state}', 0x74, state)
        p.label(name+'_store')
        p.emit('movx @dptr,a', 0xf0)
        p.label(name+'_resume')
        p.address(0x02, 'ljmp', resume)  # Skip the legacy nonvolatile save.
        p.label(name+'_legacy')
        p.emit(f'mov 0x51,#{legacy}', 0x75, 0x51, legacy)
        p.address(0x02, 'ljmp', 0x26b9 if state == 1 else 0x26e4)

    def permute_byte(name, moves):
        # Snapshot the stock byte before changing any bit: simultaneous presses
        # and releases must survive the whole permutation, with no aliasing.
        p.address(0x90, 'mov dptr,#', 0x8433)
        p.emit('movx a,@dptr', 0xe0)
        p.emit('mov r7,a', 0xff)
        mask = 255 ^ sum(1 << source for source, _ in moves)
        p.emit(f'anl a,#0x{mask:02x}', 0x54, mask)
        p.emit('mov r6,a', 0xfe)
        for source, target in moves:
            p.emit('mov a,r7', 0xef)
            p.emit(f'anl a,#0x{1 << source:02x}', 0x54, 1 << source)
            p.branch(0x60, 'jz', f'{name}_skip_{source}')
            p.emit(f'orl 0x06,#0x{1 << target:02x}', 0x43, 0x06, 1 << target)
            p.label(f'{name}_skip_{source}')
        p.emit('mov a,r6', 0xee)
        p.emit('movx @dptr,a', 0xf0)

    p.label('xinput_report')
    p.address(0x12, 'lcall', 0x2e58)
    p.address(0x90, 'mov dptr,#', STATE)
    p.emit('movx a,@dptr', 0xe0)
    p.branch(0x60, 'jz', 'xinput_done')
    p.branch(0xb4, 'cjne', 'xinput_check_sega', 1)
    p.address(0x90, 'mov dptr,#', 0x8433)
    p.emit('movx a,@dptr', 0xe0)
    p.emit('anl a,#0x03', 0x54, 3)
    p.branch(0x60, 'jz', 'xinput_done')
    p.branch(0xb4, 'cjne', 'xinput_exchange', 3)
    p.label('xinput_done')
    p.emit('ret', 0x22)
    p.label('xinput_exchange')
    p.emit('movx a,@dptr', 0xe0)
    p.emit('xrl a,#0x03', 0x64, 3)
    p.emit('movx @dptr,a', 0xf0)
    p.emit('ret', 0x22)
    p.label('xinput_check_sega')
    p.branch(0xb4, 'cjne', 'xinput_done', 2)  # Unknown state fails closed to stock.
    p.emit('mov a,0x52', 0xe5, 0x52)
    p.emit('anl a,#0x40', 0x54, 0x40)
    p.branch(0x60, 'jz', 'xinput_sega')
    # The stock dispatcher can exchange A/B and X/Y before building XInput.
    # Use the corresponding positions so the physical-button rotation is stable.
    p.label('xinput_sega_flipped')
    permute_byte('xinput_flipped', [(0,4), (1,0), (5,7), (4,5), (7,1)])
    p.emit('ret', 0x22)
    p.label('xinput_sega')
    permute_byte('xinput_sega', [(0,5), (1,0), (4,6), (5,4), (6,1)])
    p.emit('ret', 0x22)

    p.label('ps3_report')
    p.address(0x12, 'lcall', 0x237d)
    p.address(0x90, 'mov dptr,#', STATE)
    p.emit('movx a,@dptr', 0xe0)
    p.branch(0x60, 'jz', 'ps3_done')
    p.branch(0xb4, 'cjne', 'ps3_check_sega', 1)
    p.address(0x90, 'mov dptr,#', 0x8433)
    p.emit('movx a,@dptr', 0xe0)
    p.emit('anl a,#0x0c', 0x54, 0x0c)
    p.branch(0x60, 'jz', 'ps3_pressure')
    p.branch(0xb4, 'cjne', 'ps3_exchange', 0x0c)
    p.branch(0x80, 'sjmp', 'ps3_pressure')
    p.label('ps3_exchange')
    p.emit('movx a,@dptr', 0xe0)
    p.emit('xrl a,#0x0c', 0x64, 0x0c)
    p.emit('movx @dptr,a', 0xf0)
    p.label('ps3_pressure')
    p.address(0x90, 'mov dptr,#', 0x8444)
    p.emit('movx a,@dptr', 0xe0)
    p.emit('mov r7,a', 0xff)
    p.emit('inc dptr', 0xa3)
    p.emit('movx a,@dptr', 0xe0)
    p.emit('mov r6,a', 0xfe)
    p.emit('mov a,r7', 0xef)
    p.emit('movx @dptr,a', 0xf0)
    p.address(0x90, 'mov dptr,#', 0x8444)
    p.emit('mov a,r6', 0xee)
    p.emit('movx @dptr,a', 0xf0)
    p.label('ps3_done')
    p.emit('ret', 0x22)
    p.label('ps3_check_sega')
    p.branch(0xb4, 'cjne', 'ps3_done', 2)
    p.label('ps3_sega')
    permute_byte('ps3_sega', [(2,6), (3,2), (4,3), (5,4), (6,5)])
    # Pressure fields C,Z,X,A,B are contiguous. Rotate without losing the first.
    p.address(0x90, 'mov dptr,#', 0x8444)
    p.emit('movx a,@dptr', 0xe0)
    p.emit('mov r7,a', 0xff)
    for target in range(0x8444, 0x8448):
        p.address(0x90, 'mov dptr,#', target + 1)
        p.emit('movx a,@dptr', 0xe0)
        p.address(0x90, 'mov dptr,#', target)
        p.emit('movx @dptr,a', 0xf0)
    p.address(0x90, 'mov dptr,#', 0x8448)
    p.emit('mov a,r7', 0xef)
    p.emit('movx @dptr,a', 0xf0)
    p.emit('ret', 0x22)
    code, listing = p.finish()
    return code, listing, p.labels


def patch_regions(code, labels):
    return [
        (0x26b6, bytes.fromhex('75 51 04'), bytes([2]) + labels['toggle'].to_bytes(2, 'big'),
         'Start+Right: volatile Street Fighter preset; retain other profiles'),
        (0x26e1, bytes.fromhex('75 51 02'), bytes([2]) + labels['toggle_sega'].to_bytes(2, 'big'),
         'Start+Up: volatile SEGA preset; retain other profiles'),
        (0x34f4, bytes.fromhex('12 23 7d'), bytes([0x12]) + labels['ps3_report'].to_bytes(2, 'big'),
         'PS3 report postprocessing; stock builder and analog axes unchanged'),
        (0x34fb, bytes.fromhex('12 2e 58'), bytes([0x12]) + labels['xinput_report'].to_bytes(2, 'big'),
         'XInput report postprocessing; stock builder and analog axes unchanged'),
        (CODE_START, b'\xff' * len(code), code, '8051 extension in unused application ROM'),
    ]


def build(stock, updater):
    check(len(stock) == 32768 and digest(stock) == STOCK_SHA, 'Wrong stock firmware')
    check(digest(updater) == UPDATER_SHA, 'Wrong updater executable')
    encode = updater[0x4124:0x4224]
    check(len(encode) == 256 and len(set(encode)) == 256, 'Invalid byte permutation')
    decode = bytes(encode.index(i) for i in range(256))
    original = stock.translate(decode)
    check(digest(original) == DECODED_SHA, 'Wrong decoded firmware')
    check(original.translate(encode) == stock, 'Stock round trip failed')
    # This exact unmodified reset loop clears the state byte on receiver power-up.
    check(original[0x3774:0x3782] == bytes.fromhex('90 80 00 7f 00 7e 10 e4 f0 a3 df fc de fa'),
          'Startup RAM initialization changed')
    code, listing, labels = extension()
    check(CODE_START + len(code) < 0x7fc0, 'Extension overlaps device metadata')
    check(original[CODE_START:CODE_START+len(code)] == b'\xff' * len(code),
          'Extension space is not empty')
    patches = patch_regions(code, labels)
    modified = bytearray(original)
    allowed = set()
    for offset, before, after, _ in patches:
        check(len(before) == len(after) and original[offset:offset+len(before)] == before,
              f'Unexpected original instructions at 0x{offset:04x}')
        modified[offset:offset+len(after)] = after
        allowed.update(range(offset, offset+len(after)))
    modified = bytes(modified)
    encoded = modified.translate(encode)
    differences = [i for i in range(len(original)) if original[i] != modified[i]]
    check(set(differences) <= allowed, 'Unplanned byte change')
    check(encoded.translate(decode) == modified, 'Candidate round trip failed')
    check(len(encoded) == len(stock), 'Image size changed')
    check(original[:0x1000] == modified[:0x1000], 'Boot region changed')
    check(original[0x7fc0:] == modified[0x7fc0:], 'Device metadata changed')
    for start, end in [(0x237d, 0x24e5), (0x2e58, 0x2f58), (0x5881, 0x5897), (0x2073, 0x2200)]:
        check(original[start:end] == modified[start:end], 'Stock report/parser code changed')
    manifest = {
        'risk_notice': 'USE_AT_YOUR_OWN_RISK.txt',
        'status': 'UNOFFICIAL; built offline; see docs/polymega-hardware-results.json for user-reported hardware tests',
        'target': 'Retro-Bit V2 USB receiver for Saturn 2.4 GHz Wireless Pro',
        'base_source_url': SOURCE_URL,
        'base_sha256': STOCK_SHA, 'updater_sha256': UPDATER_SHA,
        'decoded_base_sha256': DECODED_SHA,
        'candidate_sha256': digest(encoded), 'decoded_candidate_sha256': digest(modified),
        'bytes': len(encoded), 'changed_bytes': len(differences),
        'default': 'Stock mapping on receiver power-up',
        'activation': 'Hold Start+Right for Street Fighter or Start+Up for SEGA, then release. Repeat the active shortcut for stock; the other selects its preset without stacking.',
        'states': {'0': 'Stock', '1': 'Street Fighter (C/Z exchange)', '2': 'SEGA (relative to Street Fighter: X/A/B actions move to A/B/C; C action moves to X)'},
        'hold_threshold': '0x0271 (625) stock macro iterations after initial chord detection; wall-clock timing requires hardware confirmation',
        'state_xdata': f'0x{STATE:04x}', 'persistent': False,
        'profiles': ['XInput (3)', 'PS3 compatibility (2)'],
        'analog': 'Unchanged stock analog-stick/trigger reports, independently verified by offline tests. Polymega must enable its in-game Analog setting.',
        'extension_symbols': {k: f'0x{v:04x}' for k, v in labels.items()},
        'patch_regions': [{'offset': f'0x{o:04x}', 'length': len(after), 'before': before.hex(),
                           'after': after.hex(), 'reason': reason} for o, before, after, reason in patches],
        'changed_offsets': [f'0x{i:04x}' for i in differences],
        'unchanged': ['Stock report builders', 'Radio parser and analog processing', 'Input mapping tables',
                      'USB descriptors', 'Pairing logic', 'Boot region', 'Device metadata',
                      'Switch and D-input shortcut behavior'],
    }
    return original, modified, encoded, manifest, listing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--updater', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original, modified, encoded, manifest, listing = build(args.stock.read_bytes(), args.updater.read_bytes())
    notice = Path(__file__).with_name('USE_AT_YOUR_OWN_RISK.txt').read_bytes()
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in [
        ('USE_AT_YOUR_OWN_RISK.txt', notice),
        (CANDIDATE_NAME, encoded), ('stock_decoded.bin', original),
        ('candidate_decoded.bin', modified),
        ('patch_manifest.json', (json.dumps(manifest, indent=2) + '\n').encode()),
        ('polymega_toggle.asm', listing.encode()),
    ]:
        write_new(args.output/name, data)
    print(json.dumps({'candidate_sha256': manifest['candidate_sha256'],
                      'changed_bytes': manifest['changed_bytes'],
                      'extension_bytes': len(extension()[0]), 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
