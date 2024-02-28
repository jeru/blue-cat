# One-off setup
* Install `zephyr` following [this page](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).
  - In theory, only `west` is needed.
    The other contents (including zephyr) will be cloned into the project by `west`.
  - **To use `west`, each shell needs `$ source ~/zephyrproject/.venv/bin/activate`.**
* Clone this git repo locally:
  ```bash
  mkdir -p ~/MyProjects
  cd ~/MyProjects
  west init -m https://github.com/jeru/blue-cat blue-cat-west-ws
  cd blue-cat-west-ws
  west update
  ```
* For the blue-cat module:
  ```bash
  cd blue-cat/apps/blue_cat
  west build -b blue_cat .
  ```
* For the blue-cat module:
  ```bash
  cd blue-cat/apps/chihuahua
  west build -b chihuahua .
  ```
* nRF52840 dongle accessibility by the `nRF Connect Desktop BLE app` (since I never got any luck on `nRF Connect Moible` when setting up the advertising): NordicSemi has [a packet](https://github.com/NordicSemiconductor/nrf-udev) for the `udev` rules. Install it.

# Each edit-test iteration
For the blue-cat module (after setting up the SWO messages in the codelab):
  ```bash
  apps/blue_cat$ west flash && west view-swo
  ```

For the chihuahua module:
  ```bash
  apps/chihuahua$ west flash && west espressif monitor
  ```

# Codelabs
Major reason to write these codelabs: a way for the future "me" to resume the project after things are forgotten.
1. [Blink an nRF52840 module](codelabs/blinky_nrf52840.md).
1. [`west flash` and SWO messages](codelabs/west_flash_and_swo.md).
1. [Connection of the nRF52840 module](codelabs/connection_bluecat.md).
1. [Blink an ESP32C3 module](codelabs/blinky_esp32c3.md).
