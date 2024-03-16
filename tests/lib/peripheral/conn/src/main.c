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

#include <stdio.h>

#include <blue_cat/peripheral/conn.h>

#define LOG_LEVEL 4
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

static void connected(struct bt_conn *conn) { LOG_INF("connected"); }

static void disconnected() { LOG_INF("disconnected"); }

static void passkey_display(int passkey) { LOG_INF("PK<%d>", passkey); }

static struct blue_cat_peripheral_conn_loop_cb default_loop_cb = {
    .peer_name = CONFIG_BT_DEVICE_NAME,
    .connected = &connected,
    .disconnected = &disconnected,
    .passkey_display = &passkey_display,
};

int main() {
    int err = blue_cat_peripheral_conn_loop_kickoff(&default_loop_cb);
    if (err != 0) {
        LOG_ERR("------ err %d ------ cannot kickoff...", err);
    }
    return 0;
}
