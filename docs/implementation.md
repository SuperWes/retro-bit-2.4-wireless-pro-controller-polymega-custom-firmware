# Start+Right toggle implementation

> **USE AT YOUR OWN RISK.** Flashing the custom image can permanently brick
> the receiver. Passing the checks described here does not
> prove that flashing or recovery will work. **V2 USB receiver only; never flash
> the controller or Saturn-port receiver.** See the
> [full risk and warranty notice](../USE_AT_YOUR_OWN_RISK.txt).

This is a binary patch to the exact official V2 USB Pro 1.1 image, not a rebuild
of vendor source. `build_polymega_toggle.py` validates the firmware and updater
hashes, decodes the vendor byte permutation, emits a labeled 8051 extension and
re-encodes the complete 32,768-byte image. The input is always the unmodified
stock image, not the earlier C/Z-swap prototype.

## Hooks and state

| Decoded ROM address | Stock operation | New operation |
| --- | --- | --- |
| `0x26b6` | `MOV 0x51,#4` after Start+Right hold | `LJMP 0x6000` to profile-aware toggle handler |
| `0x34f4` | `LCALL 0x237d`, PS3 builder | Call wrapper at `0x603f` |
| `0x34fb` | `LCALL 0x2e58`, XInput builder | Call wrapper at `0x6025` |
| `0x6000..0x6068` | Unused `0xff` application ROM | 105-byte extension |

The candidate differs from stock at 108 byte positions. The three hook regions
and extension occupy 114 bytes; some opcode bytes already equal the old bytes.
Boot bytes `0x0000..0x0fff`, device metadata `0x7fc0..0x7fff`, USB descriptors,
stock report builders, mapping tables, radio parsing and calibration are unchanged.

XDATA `0x85ff` holds the volatile flag (0 = stock, 1 = C/Z correction). The highest
identified stock application allocation is the two-byte object at `0x855c..0x855d`.
The selected byte is beyond the identified static data/buffer ranges and inside
the stock startup clear of `0x8000..0x8fff` at ROM `0x3774..0x3781`. The tests execute
that clear from nonzero memory to verify initialization. This is static analysis
of the pinned image, not a vendor linker map or a runtime memory trace.

The state is not copied into the legacy saved-layout structure and no new flash
or EEPROM write is introduced. Power-cycling the receiver clears it. A controller
disconnect or switching PC compatibility profiles alone need not clear it.

## Shortcut path

The controller GPIO scan records Start in raw bit 22 and Right in raw bit 13.
Its radio builder sends the digital state; the existing receiver macro detector
at `0x264b` inspects the cached raw bytes at `0x8526..0x8528`. No controller patch
is needed for this shortcut.

The original detector checks Start, checks Right, initializes its hold counter,
and reaches `0x26b6` once at counter `0x0271`. The counter saturates rather than
wrapping. Releasing either button rearms it through the existing detection logic.
The patch retains that timing; simulation establishes iteration counts, not the
real hardware's elapsed seconds.

At the hook, host profile `0x8542` selects behavior:

- 2 (PS3 compatibility) or 3 (XInput): if Right is the only D-pad direction,
  XOR the volatile flag with 1, then resume at `0x26c1`.
- All other profiles: execute the displaced `MOV 0x51,#4` and resume at `0x26b9`,
  preserving the existing settings-save and shortcut behavior.

The PC branch skips `0x2798` and its nonvolatile save at `0x3c98`. It leaves the
legacy layout and face-button-flip settings intact. The ordinary input change
when the chord is released refreshes the USB report. The macro does not consume
the chord's host button events or add a new LED pattern.

## Report processing and analog support

The dispatch wrappers call the original stock report builders first. With the
flag clear, they return without modifying the report. With the flag set:

- XInput: exchange the two shoulder bits in report byte 3.
- PS3: exchange L1/R1 bits in report byte 3 and their corresponding pressure
  fields in bytes 20/21.

Both-pressed and neither-pressed cases are preserved. The wrappers do not alter
the source button state, input caches, axes, triggers, D-pad, stick clicks,
Start/Select/Home or the existing ABXY-flip behavior.

The stock radio parser fills four axis bytes at `0x8520..0x8523`; its existing
calibration is unchanged. XInput reports them as signed 16-bit values with
`(input - 128) * 256`: center 0 and endpoints -32768/+32512. PS3 uses 8-bit X and
inverted Y fields. ZL/ZR retain their independent full-press trigger/button fields.
No new scaling, dead zone, D-pad emulation or right-stick mapping is introduced.

The user confirmed the stock USB left-stick path in NiGHTS into Dreams once
Polymega's in-game Analog option was enabled. The receiver supplies USB gamepad
reports; Polymega chooses the emulated Saturn controller type. Firmware on the
receiver cannot directly set that host-menu option. The new candidate preserves
the confirmed analog path and tests its output numerically in both toggle states.

## Verification boundaries

`tests/verify_polymega_toggle.cpp` executes the actual stock macro detector,
patched hook, report dispatcher, report builders and startup clear with a focused
8051 instruction interpreter. The unchanged PS3 template-copy helper is modeled
with checked operands. Legacy settings-save calls are counted and returned from;
their nonvolatile hardware is not emulated. No other called function is silently
stubbed; an unsupported opcode or unexpected helper invocation fails the test.

`tests/run_validation.py` compiles with warnings as errors, checks a byte-identical
rebuild, runs exhaustive report comparisons and analog sweeps, rejects deliberate
mutations and confirms bad input hashes create no output directory. The generated
validation file records source hashes so these results can be tied to the code.

The new extension no longer preserves the earlier prototype's byte histograms
or per-block additive sums. Static updater inspection found decoded application
programming in 32-byte packets with packet checksums constructed by the updater;
no separate file-level signature/checksum was identified in that path. That
inspection does not establish successful programming of this larger candidate.

On November 16, 2026, one user reported successful installation and C/Z toggle
operation on Polymega. This report did not separately itemize every button,
custom-firmware analog behavior, hold timing, or receiver power-cycle reset.
Recovery after a failed flash remains unverified. See the
[hardware report](polymega-hardware-results.json).
