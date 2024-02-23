# One-off setup
* Install `zephyr` following [this page](https://docs.zephyrproject.org/latest/develop/getting_started/index.html).
* Clone this git repo locally, say `${BLUE_CAT_GIT_REPO}`.

# Per shell
* Load venv by `$ source ~/zephyrproject/.venv/bin/activate`.
* Load more env vars by `$ source ${BLUE_CAT_GIT_REPO}/extra-env.sh`.

# Codelabs
Major reason to write these codelabs: a way for the future "me" to resume the project after things are forgotten.
1. [Blink an nRF52840 module](codelabs/blinky_nrf52840.md).
1. [`west flash` and SWO messages.](codelabs/west_flash_and_swo.md).
