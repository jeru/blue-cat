# Codelab: Blink the nRF52840

## Hardware setup
Very initial development of the `blue_cat` app will be done on some nRF52840 dev module before moving to its own PCB.
What's used here is the so called "nrf52840 supermini" or "nrf52840 promicro".
See [this page](https://github.com/joric/nrfmicro/wiki/Alternatives) for more info.
Note the dev module has an LED at `P0.15`.

Programming uses ARM's SWD via a DAPLink prober.
The `SWDIO` and `SWCLK` pins are exposed only as pads instead of pinheaders.
So, either solder some extra wires in, or use some pogo-pin style programmer.

## Software setup
The blink's main program is already available at `${ZEPHYR_BASE}/samples/basic/blinky/`.
This codelab is actually only trying to
(1) make a compatible board config, and
(2) run the build-and-flash iteration cycle once successfully.

With the version of board in `boards/arm/blue_cat`, to build:
```west build -b blue_cat $ZEPHYR_BASE/samples/basic/blinky```

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
