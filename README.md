# Retro-Bit Saturn Pro on Polymega

Corrects the C/Z mapping on the **Retro-Bit V2 USB receiver** for the Saturn 2.4 GHz Wireless Pro controller.

> **USE AT YOUR OWN RISK.** Unofficial firmware, supplied AS IS without warranty. Flashing can brick the receiver; recovery is not guaranteed. **V2 USB receiver only**—never the controller or Saturn-port receiver. [Full notice](USE_AT_YOUR_OWN_RISK.txt).

## Install

1. [Download the installer ZIP](https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware/releases/tag/v0.1.0-alpha.2) and extract it on Windows 10/11.
2. Double-click **Install.cmd**. It downloads Retro-Bit's official package, applies the patch locally, and opens the updater. Internet access is required; no Python or compiler is needed.
3. Follow the installation PDF in **Firmware Package**, selecting the `.bxw` in its **Firmware** folder. Wait for the update to finish before disconnecting.

## Use

- Use the working **three-green-light USB mode** on Polymega.
- Hold **Start + D-pad Right**, then release, to toggle the C/Z correction. Repeat to turn it off.
- Reconnecting the USB receiver resets to **stock mapping**. **ZL/ZR remain Saturn L/R**.
- For analog games, enable **Analog in Polymega's in-game controller settings**.

One user reported successful installation and C/Z toggle operation on Polymega on November 16, 2026. Recovery after a failed flash remains untested.

[Build and test details](docs/building.md) · [Implementation](docs/implementation.md) · [Hardware reports](docs/polymega-hardware-results.json) · [Third-party files](docs/third-party-files.md)
