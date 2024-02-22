# Codelab: Blink the nRF52840
The blink's main program is already available at `${ZEPHYR_BASE}/samples/basic/blinky/`.
The goal of this codelab is to:
1. Write a compatible board config;
2. Make the basic hardware + software setup correct for build and flash.

## Hardware setup
Initial development of the `blue_cat` app will be done on some nRF52840 dev module before moving to its own PCB.
What's used here is the so called "nrf52840 supermini" or "nrf52840 promicro".
See [this page](https://github.com/joric/nrfmicro/wiki/Alternatives) for more info.
Note the dev module has an LED at `P0.15`.

Programming uses ARM's SWD via a DAPLink prober.
The `SWDIO` and `SWCLK` pins are exposed only as pads instead of pinheaders.
So, either solder some extra wires in, or use some pogo-pin style programmer.

## Software setup
With [`boards/arm/blue_cat` at the current version](https://github.com/jeru/blue-cat/tree/a4d892a84c679e80392ba1b83712796b24212639/boards/arm/blue_cat), to build:
```$ west build -b blue_cat $ZEPHYR_BASE/samples/basic/blinky```

And to flash the baremetal way (later we will setup something better):
```
# In one window.
$ openocd -f interface/cmsis-dap.cfg -f target/nrf52.cfg
# In another window.
$ ~/zephyr-sdk-0.16.5/arm-zephyr-eabi/bin/arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :3333
(gdb) monitor reset halt
(gdb) load
(gdb) monitor reset
(gdb) exit
```
Now the board LED should start blinking.

## Clean up
```$ rm -rf build```
