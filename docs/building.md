# Build and validate


Requirements: Python 3, a C++17 compiler, and the exact `BxUsbUpdate.exe` from [Retro-Bit's official USB Pro 1.1 archive](https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip). The builder reads that executable as data; it does not run it. These commands perform no device I/O or flashing.

Build a new candidate (the output directory must not already exist):

```sh
python3 build_polymega_toggle.py --stock /path/to/official-firmware.bxw --updater /path/to/BxUsbUpdate.exe --output build/toggle
```

Run complete validation, including reproducibility and negative controls:

```sh
python3 tests/run_validation.py --stock /path/to/official-firmware.bxw --updater /path/to/BxUsbUpdate.exe
```

Add `--output build/validated-toggle` to save a verified package. Inputs are checked against exact SHA-256 fingerprints; other versions are rejected before an output directory is created.

Validation covers:

- 884,736 stock/candidate report comparisons: all 8,192 relevant digital input combinations, nine D-pad states, two PC profiles, all three presets and the existing face-button-flip option off/on.
- 1,277,952 independent analog-report checks in total, including 393,216 reports covering every left-stick X/Y pair in both profiles and all three presets.
- Actual macro and report-dispatch instructions: both shortcuts, every preset transition, hold threshold, repeat prevention, release/rearming, interrupted holds, diagonal rejection, stock legacy shortcuts, no nonvolatile save for either PC shortcut and reset to stock at receiver startup.
- Deliberately broken images rejected for missing shortcuts, missing report hooks, missing SEGA processing (including the stock face-button-flip option), inverted default behavior and corrupted analog conversion.

The interpreter models PS3's unchanged template-copy helper and observes legacy settings-save calls without emulating their nonvolatile hardware. Inputs begin after stock radio parsing/calibration. Radio, interrupts, USB negotiation, flash, the complete MCU and Polymega are not emulated. See [implementation notes](implementation.md) for patch addresses and limits.


## Firmware release ZIP

The recommended installation uses a Windows PC and Retro-Bit's official updater
downloaded separately. Package a validated build with:

```sh
python3 tools/package_firmware_release.py --firmware build/validated-toggle/retrobit_usb_pro_1.1_polymega.bxw --output build/retrobit-polymega.zip
```

The packager rejects any firmware whose size or SHA-256 differs from the checked-in
validated manifest. The ZIP contains only the `.bxw` and `README.txt`; it includes
no executable, script, vendor DLL, or vendor PDF. It contains modified vendor
firmware; see [third-party files](third-party-files.md).

## Optional Windows preparation script

The preparation script uses `Install.cmd`, `Install.ps1`, and `README.txt`. Its
PowerShell patch table is generated from the same 8051 extension as the Python
builder. Its final output must match the tested firmware SHA-256 exactly.

```sh
python3 tools/package_release.py --output build/legacy-preparation-script.zip
```

The installer downloads the pinned official ZIP, checks the archive, firmware,
updater, decoded image, and final patched image hashes, and creates the vendor's
`Firmware` and `Update Program` layout locally. It copies the vendor PDF unchanged
and adds a short README. It opens the vendor updater but performs no flashing.

`tests/test_windows_installer.py` checks the new firmware ZIP against an independent
build, reproducible packaging, rejection of altered firmware, and refusal to
overwrite an existing ZIP. It also tests the earlier script under Windows
PowerShell 5.1 without launching the updater. It checks the actual download path,
byte-for-byte output, unchanged vendor files, and rejection of wrong ZIPs,
corrupted patches, and existing output folders. Vendor files remain temporary
test inputs and are never uploaded as CI artifacts.

The root `build_cz_swap.py` is the earlier four-byte prototype and provides shared
helpers to the toggle builder. The current installer always uses the toggle.

The automated record's `hardware_tested: false`
describes the offline test run. The author's successful physical tests of both
layouts are recorded separately in [hardware results](polymega-hardware-results.json).
