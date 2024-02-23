# Codelab: Support `west flash` and SWO messaging.

## `west flash`
Supporting `west flash` with openocd + DAPLink is quite straightforward given all the existing tools inside Zephyr.
A `boards/arm/blue_cat/board.cmake` file that looks like the following should suffice:
```cmake
set(OPENOCD_NRF5_SUBFAMILY nrf52)
set(OPENOCD_NRF5_INTERFACE cmsis-dap)
include(${ZEPHYR_BASE}/boards/common/openocd-nrf5.board.cmake)
```

To verify it works, the following should work:
```
$ west build -b blue_cat $ZEPHYR_BASE/samples/basic/blinky
(successful)
$ west flash
(successful)
```
This should also make `west` commands `debug`, `debugserver` and `attach` available.

Don't forget to clean up the `build` folder before the next steps.
