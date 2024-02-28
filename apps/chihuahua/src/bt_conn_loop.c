// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

// The part of the callback hell that keeps the scan-connect-disconnect loop.

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(bt_conn_loop);

static void start_scan();

// TODO: Share the constant with the BlueCat app.
static const char m_blue_cat_name[] = "BlueCat";

// Holds a `struct bt_conn*` with referencing.
static atomic_ptr_t m_conn = ATOMIC_PTR_INIT(NULL);

static bool process_adv_data(struct bt_data* data, void* name_matched) {
    if (data->type != BT_DATA_NAME_SHORTENED &&
        data->type != BT_DATA_NAME_COMPLETE) {
        return true;  // Continue processing.
    }
    char buf[data->data_len + 1];
    memcpy(buf, data->data, data->data_len);
    buf[data->data_len] = 0;
    LOG_INF("Name: %s", buf);
    *((bool*)name_matched) =
        data->data_len == strlen(m_blue_cat_name) &&
        memcmp(data->data, m_blue_cat_name, data->data_len) == 0;
    return false;  // Seen the name. Stop processing.
}

static bool does_peer_name_match(struct net_buf_simple* adv_data) {
    bool name_matched = false;
    bt_data_parse(adv_data, process_adv_data, &name_matched);
    return name_matched;
}

static void print_found_device(const bt_addr_le_t* bt_addr, int8_t rssi) {
    char buf[BT_ADDR_LE_STR_LEN];
    bt_addr_le_to_str(bt_addr, buf, sizeof(buf));
    LOG_INF("Found device %s rssi %d", buf, rssi);
}

static void device_found(const bt_addr_le_t* bt_addr, int8_t rssi, uint8_t type,
                         struct net_buf_simple* adv_data) {
    int err;

    print_found_device(bt_addr, rssi);
    if (!does_peer_name_match(adv_data)) {
        LOG_DBG("Peer name wrong.");
        return;  // Continue scanning.
    }
    err = bt_le_scan_stop();
    if (err) {
        LOG_ERR("err %d: Failed to stop LE scan.", err);
        return;  // Supposedly the scanning is still ongoing?
    }

    struct bt_conn* conn = NULL;
    err = bt_conn_le_create(bt_addr, BT_CONN_LE_CREATE_CONN,
                            BT_LE_CONN_PARAM_DEFAULT, &conn);
    if (err) {
        LOG_ERR("err %d: Failed to initiate connection.", err);
        start_scan();
        return;
    }
    while (!atomic_ptr_cas(&m_conn, NULL, (atomic_ptr_val_t)conn)) {
        // Most likely this can happen is a misconfigure that more than one
        // connections are allowed.
        LOG_ERR("THIS LINE SHOULDN'T BE REACHABLE.");
        k_sleep(K_SECONDS(10));
    }
}

static void start_scan() {
    int err = bt_le_scan_start(BT_LE_SCAN_PASSIVE, device_found);
    if (err) LOG_ERR("err %d: Failed to start scanning.", err);
}

static void connected(struct bt_conn* conn, uint8_t err) {
    if (err) {
        LOG_WRN("err %d: Failed connection.", err);
        return;
    }
    LOG_INF("Connected.");
}

static void disconnected(struct bt_conn* conn, uint8_t reason) {
    LOG_INF("reason %d: Disconnected.", reason);
    struct bt_conn* stored_conn;
    // Somehow the disconnection happened too soon after connection is
    // initiated.
    while ((stored_conn = atomic_ptr_clear(&m_conn)) == NULL) {
        k_sleep(K_MSEC(100));
    }
    bt_conn_unref(stored_conn);

    start_scan();
}

static struct bt_conn_cb m_conn_cb = {
    .connected = &connected,
    .disconnected = &disconnected,
};

static atomic_t m_inited = ATOMIC_INIT(0);

void chihuahua_bt_conn_loop_start() {
    if (!atomic_cas(&m_inited, 0, 1)) return;  // Already called.
    int err;

    err = bt_enable(/*cb=*/NULL);
    if (err) {
        LOG_ERR("err %d: Failed bt_enable().", err);
        return;
    }
    bt_conn_cb_register(&m_conn_cb);

    start_scan();
}
