# Street Fighter and SEGA layout implementation

> **USE AT YOUR OWN RISK.** V2 USB receiver only. Flashing can brick the receiver;
> recovery is not guaranteed. Offline checks do not establish hardware safety.
> See the [full notice](../USE_AT_YOUR_OWN_RISK.txt).

This is a binary patch to the exact official V2 USB Pro 1.1 image, not a rebuild
of vendor source. The builder validates input hashes, decodes the vendor byte
permutation, emits a labeled 8051 extension, and re-encodes the complete
32,768-byte image. It always starts from the unmodified stock image.

## Hooks and state

| Decoded ROM address | Stock operation | Replacement |
| --- | --- | --- |
| `0x26b6` | `MOV 0x51,#4` after Start+Right hold | Jump to Street Fighter selector at `0x6000` |
| `0x26e1` | `MOV 0x51,#2` after Start+Up hold | Jump to SEGA selector at `0x602b` |
| `0x34f4` | Call PS3 builder `0x237d` | Call wrapper at `0x60e2` |
| `0x34fb` | Call XInput builder `0x2e58` | Call wrapper at `0x6056` |
| `0x6000..0x616e` | Unused `0xff` application ROM | 367-byte extension |

The candidate differs from stock at 368 byte positions. The four hooks and
extension occupy 379 bytes; some opcode bytes equal the original bytes. Boot
bytes `0x0000..0x0fff`, metadata `0x7fc0..0x7fff`, USB descriptors, stock report
builders, mapping tables, radio parsing, calibration and pairing are unchanged.
The Python builder and legacy PowerShell packager share one patch definition.

XDATA `0x85ff` holds one exclusive preset: **0 stock, 1 Street Fighter, 2 SEGA**.
Unknown values produce stock reports. The highest identified stock application
allocation is `0x855c..0x855d`. The chosen byte is beyond identified static buffers
and inside the unchanged startup clear of `0x8000..0x8fff`. Tests execute that
clear from nonzero memory. This allocation is based on static analysis of the
pinned image, not a vendor linker map or a runtime memory trace.

The state is never saved to flash or EEPROM. Power-cycling the receiver resets
it; a controller disconnect or PC-profile change alone need not reset it.

## Shortcuts

Raw Start is bit 22, Right bit 13, and Up bit 14. The existing macro detector at
`0x264b` examines cached raw bytes `0x8526..0x8528`. Both shortcuts reach their
hooks once at counter `0x0271` (625 iterations after initial detection). The
counter saturates; releasing either button rearms it. This establishes iteration
counts, not elapsed seconds on hardware.

For host profile `0x8542` equal to 2 (PS3 compatibility) or 3 (XInput), the selected
direction must be the only D-pad direction. Start+Right selects 1; Start+Up selects
2. Selecting the active preset returns to 0. Selecting the other replaces it;
there is no stacked C/Z flag. Both PC paths skip the legacy nonvolatile save,
resuming at `0x26c1` or `0x26ec`.

Other host profiles execute the displaced stock instruction and resume at
`0x26b9` or `0x26e4`, retaining the original shortcuts and saves. The PC selectors
preserve the legacy layout and face-button-flip settings. The normal input change
on release refreshes the USB report. Shortcuts are not consumed from host input
and there is no new LED indicator.

## Physical mapping and reports

The guided Mac capture in Switch-compatible USB mode recorded A/B/X/Y as report
byte 0 masks `08/04/02/01`. The stock Switch table at `0x57c0` maps raw bits
8/9/10/11 to report bits 3/2/1/0 respectively, grounding their physical identities.
C and L share raw bit 16; Z and R share bit 18. ZL and ZR are raw bits 7 and 6.
The duplicate pairs cannot be separated by this receiver-only patch.

Each wrapper calls the stock builder first. The selected preset then permutes
only face/shoulder outputs, including the corresponding PS3 pressure fields.
Here “stock X,” for example, means the USB output sent by physical X under
stock firmware, not an assertion about an emulated Saturn button:

| Physical button | Stock | Street Fighter | SEGA |
| --- | --- | --- | --- |
| A | Stock A | Stock A | Stock X |
| B | Stock B | Stock B | Stock A |
| C / L | Stock C | Stock Z | Stock B |
| X | Stock X | Stock X | Stock Z |
| Y | Stock Y | Stock Y | Stock Y |
| Z / R | Stock Z | Stock C | Stock C |
| ZL / ZR | Unchanged | Unchanged | Unchanged |

Thus SEGA moves Street Fighter-layout X/A/B actions to A/B/C, and C's action to
X. It is intended for the three-button SEGA arrangement when a host adapts it to
a four-face-button pad. It does not identify games or change host configuration.
The user's Nanatsu Kaze observations motivated it; that is not its preset name.

Street Fighter exchanges XInput byte 3 bits 0/1, or PS3 byte 3 bits 2/3 and
pressure bytes 20/21. This preserves the earlier C/Z-only behavior.

SEGA permutes XInput byte 3 using a snapshot, preserving simultaneous presses.
The existing ABXY-flip option changes the stock XInput positions; the wrapper
selects the matching permutation so the physical rotation above still holds.
PS3 byte 3 uses its corresponding permutation; pressure bytes 20..24 rotate
from `[C,Z,X,A,B]` to `[Z,X,A,B,C]`. PS3's stock builder ignores that flip option.

The report wrappers do not modify source inputs, caches, analog values, D-pad,
stick clicks, Start/Select/Home or ZL/ZR. The original dispatcher may still apply
its existing ABXY flip before calling a builder.

## Analog path and verification limits

The unchanged radio parser supplies four axis bytes at `0x8520..0x8523`.
XInput reports signed 16-bit `(input - 128) * 256` (center 0, endpoints
-32768/+32512). PS3 uses 8-bit X and inverted Y fields. ZL/ZR retain independent
trigger/button fields. No scaling, dead zone or stick-to-D-pad conversion is added.
The user confirmed stock USB analog in NiGHTS into Dreams after enabling Analog
in Polymega's in-game settings. Receiver firmware cannot set that host option.

The tests execute the actual macro detector, hooks, dispatcher, stock builders,
extension and startup clear in a focused 8051 instruction interpreter. PS3's
unchanged ROM-template copy is modeled with checked operands; legacy settings
saves are counted without emulating nonvolatile hardware. Unsupported instructions
or unexpected helpers fail. The report oracle permutes physical raw inputs before
running the original ROM, independently of the extension's USB-field algorithm.
It checks every relevant simultaneous button combination, all presets and the
stock face-flip option. Explicit single-button expectations guard mapping direction.

Rebuilds, negative controls, all preset transitions, diagonal rejection, reset,
legacy shortcuts, numeric analog sweeps and package checks are described in
[building](building.md). Radio, interrupts, USB negotiation, flashing and Polymega
itself are not emulated. The generated validation record includes source hashes.

The earlier C/Z-only image was reported installed and working in a fighting game
on one Polymega setup. It did not fix every game. On November 16, 2026, the author
then reported testing both
Street Fighter and SEGA layouts on their receiver with Polymega, saying both
work great. This confirms one user's setup, not every host or game.
Static updater inspection found application writes in
32-byte packets with updater-created checksums; no separate file signature was
identified in that path. Neither that analysis nor preserved boot bytes establishes
safe flashing or recovery. See the [hardware observations](polymega-hardware-results.json).
