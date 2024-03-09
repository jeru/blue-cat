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

#include <blue_cat/central/conn.h>

#define LOG_LEVEL 4
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(main);

static void connected(struct bt_conn* conn) {
    LOG_INF("connected");
}

static void disconnected() {
    LOG_INF("disconnected");
}

static void passkey_display(int passkey) {
    LOG_INF("passkey_display: ", passkey);
}

static int passkey_entry() {
    LOG_INF("passkey_entry");

    char line[128];
    if (!fgets(line, sizeof(line), stdin)) return -1;

    int passkey;
    if (sscanf(line, "PK%dPK", &passkey) < 0) return -1;
    return passkey;
}

static bool passkey_confirm(int passkey) {
    LOG_INF("passkey_confirm");
    return true;
}

static struct blue_cat_central_conn_loop_cb default_loop_cb = {
    .peer_name = "TestPeerName",
    .connected = &connected,
    .disconnected = &disconnected,
    .passkey_display = &passkey_display,
    .passkey_entry = &passkey_entry,
    .passkey_confirm = &passkey_confirm,
};

int main() {
    blue_cat_central_conn_loop_kickoff(&default_loop_cb);
    return 0;
}
