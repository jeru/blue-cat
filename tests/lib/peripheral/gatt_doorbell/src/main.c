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

#include <zephyr/bluetooth/conn.h>

#include <blue_cat/peripheral/conn.h>
#include <blue_cat/peripheral/gatt_doorbell.h>

#define LOG_LEVEL 4
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

static void passkey_display(int passkey) {}

static struct blue_cat_peripheral_conn_loop_cb default_loop_cb = {
    .peer_name = CONFIG_BT_DEVICE_NAME,
    .passkey_display = &passkey_display,
};

int main() {
    int err;
    err = blue_cat_peripheral_conn_loop_kickoff(&default_loop_cb);
    if (err != 0) {
        LOG_ERR("------ err %d ------ cannot kickoff...", err);
        return 0;
    }
    // TEST ONLY! DON'T DO IT IN PROD!
    err = bt_passkey_set(321098);
    if (err != 0) {
        LOG_ERR("------ err %d ------ cannot set fixed passkey...", err);
        return 0;
    }
    LOG_INF("Passkey set.");
    for (int x = 0;; ++x) {
        k_sleep(K_MSEC(500));
        blue_cat_gatt_doorbell_ring_write(x % 2 ? 123 : 456);
    }
    return 0;
}
