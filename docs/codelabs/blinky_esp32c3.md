# Blink an ESP32C3 module
Initial development is done with an ESP32C3 Supermini module.

NOTE: Due to the concerning heat dissapation on this tiny board, and the system's need to run stably for very long time, consider a custom PCB on an offical ESP32-C3-WROOM module with heatsink vias.

Board definition checked in as `boards/riscv/chihuahua/*`.
To initialize the cmake building:
```bash
blue-cat-west-ws/blue-cat$ west build -b chihuahua ../zephyr/samples/basic/blinky
```

Then to flash and test:
```bash
$ west flash
```
This starts blinking a blue LED.
(The red LED seems to be the power supply indicator.)

To monitor the messages:
```bash
$ west espressif monitor
```
