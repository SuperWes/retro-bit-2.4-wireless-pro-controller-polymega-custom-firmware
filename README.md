# Retro-Bit Saturn Pro on Polymega

On Polymega, the stock mapping has **C and Z reversed**. This patch for the **Retro-Bit V2 USB receiver** and Saturn 2.4 GHz Wireless Pro controller adds a toggle for that swap. The rest of the stock mapping is preserved; the duplicate L/R buttons follow C/Z.

> **USE AT YOUR OWN RISK.** Unofficial firmware, supplied AS IS without warranty. Flashing can brick the receiver; recovery is not guaranteed. **V2 USB receiver only**—never the controller or Saturn-port receiver. [Full notice](USE_AT_YOUR_OWN_RISK.txt).

## Install

**You need a Windows PC to install the firmware.**

1. [Download the custom firmware ZIP](https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware/releases/tag/v0.1.0-alpha.5) and extract it.
2. Download and fully extract [Retro-Bit's official V2 USB Pro 1.1 package](https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip). It contains the official Windows updater and installation PDF.
3. Follow that PDF and run **BxUsbUpdate.exe** from its **Update Program** folder, keeping its DLLs alongside it. When choosing firmware, select **retrobit_usb_pro_1.1_polymega_toggle_EXPERIMENTAL.bxw** from this project's ZIP in place of the official `.bxw`. Wait for the update to finish before disconnecting.
4. **Re-sync (pair) the receiver with the controller after updating**, before playing.

The custom ZIP contains the ready-made firmware and a short README. No project installer, Python, or compiler is needed. Using the official updater does not remove the risks of flashing unofficial firmware.

## Use

- Use USB mode with **two green lights on Polymega** (**three on Mac**).
- Hold **Start + D-pad Right**, then release, to swap C and Z. Repeat to restore stock mapping.
- Reconnecting the USB receiver resets to **stock mapping**. **ZL/ZR remain Saturn L/R**.
- For analog games, enable **Analog in Polymega's in-game controller settings**.

The same receiver may also help on other USB hosts with reversed C/Z in XInput or PS3 mode; those hosts are untested.

One user reported successful installation and C/Z toggle operation on Polymega on November 16, 2026. Recovery after a failed flash remains untested.

[Build and test details](docs/building.md) · [Implementation](docs/implementation.md) · [Hardware reports](docs/polymega-hardware-results.json) · [Third-party files](docs/third-party-files.md)
