Retro-Bit Saturn Pro on Polymega

USE AT YOUR OWN RISK. Unofficial firmware; supplied AS IS without
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
