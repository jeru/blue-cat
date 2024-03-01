// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#include <blue_cat/central/conn.h>
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/console/console.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static void connected_cb(struct bt_conn* conn) {
    LOG_INF("Connected.");
}

// Returns -1 for invalid.
static int32_t parse_6digit_number(char* s) {
    int32_t num = 0;
    const int N = 6;
    for (int i = 0; i < N; ++i) {
        if (s[i] < '0' || s[i] > '9') return -1;
        num = num * 10 + (s[i] - '0');
    }
    if (s[N] != '\0') return -1;
    return num;
}

static void passkey_display(int passkey) {
    LOG_INF("Passkey display: %.6u", passkey);
}

static int passkey_entry() {
    for (;;) {
        LOG_INF("Input passkey needed. 6 Digits or 'n':");
        char* s = console_getline();
        if (s[0] == 'n') return -1;
        int32_t passkey = parse_6digit_number(s);
        if (passkey == -1) {
            LOG_ERR("Invalid passkey. Again? 6 digits or 'n'.");
            continue;
        }
        return passkey;
    }
}

static bool passkey_confirm(int passkey) {
    LOG_INF("Confirm [y/n]? Passkey: %.6u", passkey);
    for (;;) {
        char* s = console_getline();
        if (s[0] == 'y') return true;
        if (s[0] == 'n') return false;
        LOG_INF("Invalid. again [y/n]?");
    }
}

static struct blue_cat_central_conn_loop_cb loop_cb = {
    // TODO: Share the constant with the BlueCat app.
    .peer_name = "BlueCat",
    .connected = &connected_cb,
    .passkey_display = &passkey_display,
    .passkey_entry = &passkey_entry,
    .passkey_confirm = &passkey_confirm,
};

int main() {
    int err;
    err = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (err) {
        LOG_ERR("err %d: Failed to make the LED pin output.", err);
        return err;
    }
    console_getline_init();
    blue_cat_central_conn_loop_kickoff(&loop_cb);
    for (;;) {
        // Intentionally different from the blinky example to show a visible
        // difference if logging doesn't work.
        k_sleep(K_MSEC(500));

        (void)gpio_pin_toggle_dt(&led);  // Ignore the error.
    }
    return 0;
}
