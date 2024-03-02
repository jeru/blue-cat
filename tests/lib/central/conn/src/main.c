// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

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
    return -1;
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
