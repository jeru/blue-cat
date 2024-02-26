// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

// The part of the callback hell that keeps the advertising-connect-disconnect
// loop.

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(bt_conn_loop);

static const struct bt_data m_adv_data[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_SOME,
                  BT_UUID_16_ENCODE(BT_UUID_BAS_VAL)),
};

static void start_advertising() {
    int err = bt_le_adv_start(BT_LE_ADV_CONN_NAME_AD,
                              m_adv_data, ARRAY_SIZE(m_adv_data),
                              /*sd=*/NULL, /*sd_len=*/0);
    if (err) LOG_ERR("err %d: Failed to start adv.", err);
}

static void stop_advertising() {
    int err = bt_le_adv_stop();
    if (err) LOG_ERR("err %d: Failed to stop adv.", err);
}

static atomic_ptr_t m_user_conn_cb = ATOMIC_PTR_INIT(NULL);

void blue_cat_bt_conn_loop_conn_cb_register(
        void (*user_connected)(struct bt_conn* conn)) {
    atomic_ptr_set(&m_user_conn_cb, (atomic_ptr_val_t)user_connected);
}

static void connected(struct bt_conn* conn, uint8_t err) {
    if (err) {
        LOG_WRN("err %d: Failed connection.", err);
        return;
    }
    stop_advertising();
    void (*user_connected)(struct bt_conn* conn) =
        atomic_ptr_get(&m_user_conn_cb);
    if (user_connected) user_connected(conn);
}

static void disconnected(struct bt_conn* conn, uint8_t reason) {
    if (reason) LOG_INF("reason %d: Disconnected.", reason);
    start_advertising();
}

static struct bt_conn_cb m_conn_cb = {
    .connected = &connected,
    .disconnected = &disconnected,
};

static atomic_t m_inited = ATOMIC_INIT(0);

void blue_cat_bt_conn_loop_start() {
    if (!atomic_cas(&m_inited, 0, 1)) return;  // Already called.

    bt_conn_cb_register(&m_conn_cb);
    start_advertising();
}

