Retro-Bit Saturn Pro on Polymega

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
   retrobit_usb_pro_1.1_polymega_toggle_EXPERIMENTAL.bxw
   Use it in place of the official .bxw file. Keep the receiver connected
   until the update finishes.
5. Re-sync (pair) the receiver with the controller after updating.

No project installer, Python, or compiler is needed. The official updater does
not make custom firmware risk-free. This ZIP includes modified Retro-Bit
firmware; it does not include their updater, DLLs, or manual. Permission to
redistribute the underlying vendor firmware has not been established.

USE
Stock mapping on Polymega has C and Z reversed. Hold Start + D-pad Right,
then release, to toggle that swap. Repeat to restore stock mapping.
Reconnecting the USB receiver resets to stock. The rest of the mapping is
preserved; duplicate L/R buttons follow C/Z. ZL/ZR remain Saturn L/R.
Use two green lights on Polymega (three on Mac). For analog games, enable
Analog in Polymega's own in-game controller settings.

The firmware is unchanged from the previous release. An already working
receiver does not need another update. Other USB hosts with the same C/Z
issue may benefit, but are untested. Recovery after a failed flash is untested.

Project, full risk notice, and technical details:
https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware
