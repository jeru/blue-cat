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

## Own program with `LOG_INF()` and LED.
Add a hello-world as `apps/blue_cat/src/main.c` (at the [current version](https://github.com/jeru/blue-cat/tree/172ea8d9b8707ebef64e78d794d7a6d9578cd712/apps/blue_cat/src/main.c), toggling LED with a different frequency than the `blinky` example, and logging messages with `LOG_INF`), a basic `CMakeLists.txt` under the project, and a project config (`prj.conf`) as:
```
CONFIG_GPIO=y
CONFIG_LOG=y
CONFIG_LOG_BACKEND_SWO=y
```
Then build and flash:
```
$ west build -b blue_cat apps/blue_cat && west flash
```
The LED blinks with a different speed now.

## Make the messages show up via SWO.
The product specification of nRF52840 showed the SWO pin is `P1.00`.
Connect the DAPLink's SWO/TDO pin to this pin of the module.

For the ease of debugging why SWO doesn't work, start with direct openocd:
```
$ openocd -f apps/blue_cat/openocd.cfg -d
...
Info : 164 85 cmsis_dap.c:1048 cmsis_dap_get_swo_buf_sz(): CMSIS-DAP: SWO Trace Buffer Size = 8192 bytes
Info : 165 86 cmsis_dap.c:1932 cmsis_dap_config_trace(): SWO frequency: 1000000 Hz.
Info : 166 86 cmsis_dap.c:1933 cmsis_dap_config_trace(): SWO prescaler: 32.
Info : 167 91 gdb_server.c:3791 gdb_target_start(): starting gdb server for nrf52.cpu on 3333
Info : 168 91 server.c:297 add_service(): Listening on port 3333 for gdb connections
Info : 169 3517 server.c:90 add_connection(): accepting 'tcl' connection on tcp/6666
...
```
Now, open a SWO viewer and connect to :6666. One such viewer, from another terminal run:
```
$ python3 swo_parser.py
...
[00:00:08.898,406] <inf> main: Hello, loop.
...
```

The openocd config at the [current version](https://github.com/jeru/blue-cat/tree/172ea8d9b8707ebef64e78d794d7a6d9578cd712/apps/blue_cat/openocd.cfg).

The utility `swo_parser.py` is authored by [robertlong13](https://github.com/robertlong13/SWO-Parser/tree/master).

Calling `openocd` + `swo_parser` separately is obviously not satisfying enough for a smooth flow.

## Integrate SWO viewer
As of Feb 2024, Zephyr's use of OpenOcd via a Runner doesn't support further command expansion.
So it seems the best bet is to add a `west` extension so we get a new command to view the SWO.

Also, `swo_parser` reads the port `:6666` with a python socket object, so lacks reconnection support when the server side is gone then resumed.
So a named pipe might be a better means of communication.
Rust's `itm` crate provides an executable `itmdump` for that.

New setup reconfigured the board to not use `openocd-nrf5.board.cmake` with variables, instead use `${BOARD_DIR}/support/openocd.cfg` with `openocd.board.cmake`.
This same opencfg config is also used by the newly extended command `west view-swo` to run an openocd server with the TPIU/SWO enabled.
Now it looks like this:
```
$ west flash
(built and programmed successfully.)
$ west view-swo
...
Info : CMSIS-DAP: SWO Trace Buffer Size = 8192 bytes
Info : SWO frequency: 1000000 Hz.
Info : SWO prescaler: 32.
Info : starting gdb server for nrf52.cpu on 3333
Info : Listening on port 3333 for gdb connections
[00:00:05.334,686] <inf> main: Hello, loop.
[00:00:05.834,777] <inf> main: Hello, loop.
[00:00:06.334,838] <inf> main: Hello, loop.
...
```
The last few lines with `main: Hello, loop.` are the repeated debug info output by the board.
