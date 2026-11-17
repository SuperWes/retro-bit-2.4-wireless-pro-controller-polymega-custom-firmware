# Retro-Bit Saturn Pro on Polymega

Two optional button layouts for the **Retro-Bit V2 USB receiver** and Saturn 2.4 GHz Wireless Pro controller. Stock remains the default. The original C/Z swap worked in the fighting-game test, but did not correct the layout in *Nanatsu Kaze no Shima Monogatari*.

**Alpha.6 adds SEGA layout and has passed offline checks; this new firmware has not yet been tested on a receiver.** Earlier firmware's Street Fighter (C/Z-only) layout was reported working on one Polymega setup.

> **USE AT YOUR OWN RISK.** Unofficial firmware, supplied AS IS without warranty. Flashing can brick the receiver; recovery is not guaranteed. **V2 USB receiver only**—never the controller or Saturn-port receiver. [Full notice](USE_AT_YOUR_OWN_RISK.txt).

## Install

**You need a Windows PC to install the firmware.**

1. [Download the custom firmware ZIP](https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware/releases/tag/v0.1.0-alpha.6) and extract it.
2. Download and fully extract [Retro-Bit's official V2 USB Pro 1.1 package](https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip). It contains the official Windows updater and installation PDF.
3. Follow that PDF and run **BxUsbUpdate.exe** from its **Update Program** folder, keeping its DLLs alongside it. When choosing firmware, select **retrobit_usb_pro_1.1_polymega_toggle_EXPERIMENTAL.bxw** from this project's ZIP in place of the official `.bxw`. Wait for the update to finish before disconnecting.
4. **Re-sync (pair) the receiver with the controller after updating**, before playing.

The custom ZIP contains the ready-made firmware and a short README. No project installer, Python, or compiler is needed. Using the official updater does not remove the risks of flashing unofficial firmware.

## Use

Use USB mode with **two green lights on Polymega** (**three on Mac**). Hold the shortcut, then release:

| Shortcut | Layout | Change |
| --- | --- | --- |
| **Start + Right** | **Street Fighter** | Swap C and Z. |
| **Start + Up** | **SEGA** | From Street Fighter layout, move X/A/B actions to A/B/C and C's action to X. |

Repeating the active shortcut restores **stock**. The other shortcut switches directly to its layout; they do not stack. Reconnecting the receiver restores stock.

SEGA layout targets games whose A/B/C actions fall on physical X/A/B. Y, Z, ZL and ZR keep their Street Fighter-layout outputs. Duplicate shoulder L/R follow C/Z. For analog games, enable **Analog in Polymega's in-game controller settings**.

These are manual presets, not automatic game detection or a promise that every game uses the same mapping. Other hosts, including Evercade, are untested.

[Build and test details](docs/building.md) · [Implementation](docs/implementation.md) · [Hardware reports](docs/polymega-hardware-results.json) · [Third-party files](docs/third-party-files.md)
