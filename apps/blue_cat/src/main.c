// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

extern void blue_cat_bt_conn_loop_conn_cb_register(
        void (*user_connected)(struct bt_conn* conn));
extern void blue_cat_bt_conn_loop_start();

static void connected(struct bt_conn*) {
    LOG_INF("Connected!");
}

int main() {
    int err;
    err = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (err) {
        LOG_ERR("err %d: Failed to make the LED pin output.", err);
        return err;
    }
    blue_cat_bt_conn_loop_conn_cb_register(connected);
    blue_cat_bt_conn_loop_start();
    for (;;) {
        // Intentionally different from the blinky example to show a visible
        // difference if logging doesn't work.
        k_sleep(K_MSEC(500));

        (void)gpio_pin_toggle_dt(&led);  // Ignore the error.
        LOG_INF("Hello, loop.");
    }
    return 0;
}
