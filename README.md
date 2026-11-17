# Retro-Bit Saturn Pro on Polymega

On Polymega, the stock mapping has **C and Z reversed**. This patch for the **Retro-Bit V2 USB receiver** and Saturn 2.4 GHz Wireless Pro controller adds a toggle for that swap. The rest of the stock mapping is preserved; the duplicate L/R buttons follow C/Z.

> **USE AT YOUR OWN RISK.** Unofficial firmware, supplied AS IS without warranty. Flashing can brick the receiver; recovery is not guaranteed. **V2 USB receiver only**—never the controller or Saturn-port receiver. [Full notice](USE_AT_YOUR_OWN_RISK.txt).

## Install

1. [Download the installer ZIP](https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware/releases/tag/v0.1.0-alpha.4) and extract it on Windows 10/11.
2. Double-click **Install.cmd**. It downloads Retro-Bit's official package, applies the patch locally, and opens the updater. Internet access is required; no Python or compiler is needed.
3. Follow the installation PDF in **Firmware Package**, selecting the `.bxw` in its **Firmware** folder. Wait for the update to finish before disconnecting.
4. **Re-sync (pair) the receiver with the controller after updating**, before playing.

## Use

- Use USB mode with **two green lights on Polymega** (**three on Mac**).
- Hold **Start + D-pad Right**, then release, to swap C and Z. Repeat to restore stock mapping.
- Reconnecting the USB receiver resets to **stock mapping**. **ZL/ZR remain Saturn L/R**.
- For analog games, enable **Analog in Polymega's in-game controller settings**.

The same receiver may also help on other USB hosts with reversed C/Z in XInput or PS3 mode; those hosts are untested.

One user reported successful installation and C/Z toggle operation on Polymega on November 16, 2026. Recovery after a failed flash remains untested.

[Build and test details](docs/building.md) · [Implementation](docs/implementation.md) · [Hardware reports](docs/polymega-hardware-results.json) · [Third-party files](docs/third-party-files.md)
