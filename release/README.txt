Retro-Bit Saturn Pro on Polymega - Version 1.0

USE AT YOUR OWN RISK. Unofficial firmware, supplied AS IS without warranty.
Flashing can brick the receiver; recovery is not guaranteed.
V2 USB RECEIVER ONLY. Never flash the controller, Saturn-port receiver, or V1.

INSTALL - A WINDOWS PC IS REQUIRED
1. Extract this custom firmware ZIP.
2. Download and fully extract Retro-Bit's official V2 USB Pro 1.1 package:
   https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip
3. Follow the installation PDF in that official package. Run BxUsbUpdate.exe
   from its Update Program folder, keeping the supplied DLLs alongside it.
4. When the updater asks for firmware, select this ZIP's file:
   retrobit_usb_pro_1.1_polymega.bxw
   Use it in place of the official .bxw file. Keep the receiver connected
   until the update finishes.
5. Re-sync (pair) the receiver with the controller after updating.

No project installer, Python, or compiler is needed. The official updater does
not make custom firmware risk-free. This ZIP includes modified Retro-Bit
firmware; it does not include their updater, DLLs, or manual. Permission to
redistribute the underlying vendor firmware has not been established.

USE
Use USB mode with two green lights on Polymega (three on Mac).
Hold a shortcut, then release:
- Start + Right: Street Fighter layout (C/Z swap).
- Start + Up: SEGA layout. Relative to Street Fighter layout, X/A/B actions
  move to A/B/C and C's action moves to X. Y/Z/ZL/ZR keep the same outputs.
Repeat the active shortcut for stock. The other selects its layout directly;
they do not stack. Reconnecting the receiver restores stock.
Duplicate shoulder L/R follow C/Z. For analog games, enable Analog in
Polymega's own in-game controller settings.

SEGA layout targets games whose A/B/C actions fall on physical X/A/B.
These are manual presets; the receiver does not identify games. These custom
presets have not been separately confirmed on other hosts.

Both layouts were tested and reported working on the author's receiver with
Polymega. This is one setup's result; recovery after a failed flash remains
untested.

Project, full risk notice, and technical details:
https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware
