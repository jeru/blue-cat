// Copyright 2024 Cheng Sheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

#include <blue_cat/common/ids.h>
#include <blue_cat/peripheral/conn.h>
#include <blue_cat/peripheral/gatt_doorbell.h>

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static void passkey_display(int passkey) {
    LOG_INF("Passkey: %.6d", passkey);
}

static struct blue_cat_peripheral_conn_loop_cb loop_cb = {
    .peer_name = CONFIG_BT_DEVICE_NAME,
    .passkey_display = &passkey_display,
};

int main() {
    if (CONFIG_BT_DEVICE_NAME != BLUE_CAT_PERIPHERAL_DEVICE_NAME) {
        LOG_ERR("err: Inconsistent CONFIG_BT_DEVICE_NAME and "
                "BLUE_CAT_PERIPHERAL_DEVICE_NAME");
        return -EINVAL;
    }
    int err;
    err = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (err) {
        LOG_ERR("err %d: Failed to make the LED pin output.", err);
        return err;
    }
    err = blue_cat_peripheral_conn_loop_kickoff(&loop_cb);
    if (err) {
        LOG_ERR("err %d: Failed to kickoff the conn loop.", err);
        return err;
    }
    for (uint32_t x = 0;; ++x) {
        // Intentionally different from the blinky example to show a visible
        // difference if logging doesn't work.
        k_sleep(K_MSEC(2000));

        (void)gpio_pin_toggle_dt(&led);  // Ignore the error.
        LOG_INF("Hello, loop.");
        blue_cat_gatt_doorbell_ring_write(x % 32 < 16 ? -1 : x);
    }
    return 0;
}
