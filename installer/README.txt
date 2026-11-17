Retro-Bit Saturn Pro on Polymega

USE AT YOUR OWN RISK. Unofficial, experimental firmware; supplied AS IS without
warranty or promised repair/replacement. Flashing can brick your receiver;
recovery is not guaranteed. V2 USB RECEIVER ONLY, never the controller itself,
Saturn-port receiver, or V1 receiver.

INSTALL (Windows 10/11, internet connection required)
1. Extract this ZIP completely, then double-click Install.cmd.
2. The installer downloads Retro-Bit's official files, applies the patch locally,
   and opens the updater. No Python, compiler, or manual build is needed.
3. Read the installation PDF in the new Firmware Package folder. Follow its
   receiver-update procedure, selecting the .bxw from Firmware Package\Firmware.
   Keep the receiver connected until the updater finishes.
4. Re-sync (pair) the receiver with the controller after updating, before playing.

USE
Stock mapping on Polymega has C and Z reversed. This patch only toggles that
swap; the rest of the stock mapping is preserved. Duplicate L/R buttons follow C/Z.
Use USB mode with two green lights on Polymega (three on Mac). Hold Start +
D-pad Right, then release, to swap C and Z. Repeat to restore stock mapping.
Reconnecting the USB receiver resets to stock mapping. ZL/ZR remain Saturn L/R.
For analog games, enable Analog in Polymega's in-game controller settings.

The same receiver may help other USB hosts with reversed C/Z in XInput or PS3
mode; those hosts are untested.

One user reported successful installation and C/Z toggle operation on Polymega.
Recovery after a failed flash remains untested. Vendor files are obtained
directly from Retro-Bit during setup; this ZIP contains only project files.

Project, full risk notice, and technical details:
https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware
