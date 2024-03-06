// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

#include <blue_cat/peripheral/conn.h>

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static void passkey_display(int passkey) {
    LOG_INF("Passkey: %.6d", passkey);
}

static struct blue_cat_peripheral_conn_loop_cb loop_cb = {
    .peer_name = CONFIG_BT_DEVICE_NAME,
    .passkey_display = &passkey_display,
};

int main() {
    int err;
    err = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (err) {
        LOG_ERR("err %d: Failed to make the LED pin output.", err);
        return err;
    }
    err = blue_cat_peripheral_loop_kickoff(&loop_cb);
    if (err) {
        LOG_ERR("err %d: Failed to kickoff the conn loop.", err);
        return err;
    }
    for (;;) {
        // Intentionally different from the blinky example to show a visible
        // difference if logging doesn't work.
        k_sleep(K_MSEC(500));

        (void)gpio_pin_toggle_dt(&led);  // Ignore the error.
        LOG_INF("Hello, loop.");
    }
    return 0;
}
