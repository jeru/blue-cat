# blue-cat
A module to add some smartness in an old doorbell system; and a little bit beyond the module.

The doorbell system suffers from the following problem:
* Too mechanical: it rings only as long as a guest has the button pressed. As soon as they release the button, the ringing stops.
* Volume too low: cannot hear it clearly a little far away from the doorbell control panel.
Furthermore, there is no near-by power plug to the doorbell control panel.

## Design
* The `blue-cat` module itself:
  - battery-powered (like CR2032, not beefy LiPos);
  - simply listen to the doorbell ringing via GPIO;
  - when ringed, send out a notification via BLE to another, less location-constraint module called `chihuahua`.
* The `chihuahua` module:
  - wall-powered;
  - when notified by `blue-cat`, plays a ringtone of at least some length;
  - keep a track of ring history.

 Some "natural" choices:
 * The `blue-cat` module: nRF52840-based, with a custom PCB to sense (1) the doorbell voltage driving the speaker; and (2) the battery level.
 * The `chihuahua` module: ESP32-C3-based, connecting to a speaker via some I2S-based module.
   - The ring history can be exposed as some web-server in the intra-net via WiFi.
 * The BLE connection between them needs some security attention.
 * [`Zephyr`](https://github.com/zephyrproject-rtos/zephyr) as the development platform.
   - It should support nRF very well.
   - Though might be a little bumpy for the ESP (some basic features still missing, so maybe the support is not very mature?). Backup plan is to use ESP's SDK.
