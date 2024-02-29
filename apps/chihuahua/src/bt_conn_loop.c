// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

// The part of the callback hell that keeps the scan-connect-disconnect loop.

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/console/console.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(bt_conn_loop);

static void start_scan();

// TODO: Share the constant with the BlueCat app.
static const char m_blue_cat_name[] = "BlueCat";

// Holds a `struct bt_conn*` with referencing.
static atomic_ptr_t m_conn = ATOMIC_PTR_INIT(NULL);

static atomic_ptr_t m_user_conn_cb = ATOMIC_PTR_INIT(NULL);

void chihuahua_bt_conn_loop_connected_callback_register(
        void (*cb)(struct bt_conn* conn)) {
    atomic_ptr_set(&m_user_conn_cb, (atomic_ptr_val_t)cb);
}

static void run_connected_callback(struct bt_conn* conn) {
    void (*cb)(struct bt_conn* conn) = atomic_ptr_get(&m_user_conn_cb);
    if (cb != NULL) cb(conn);
}

static bool process_adv_data(struct bt_data* data, void* name_matched) {
    if (data->type != BT_DATA_NAME_SHORTENED &&
        data->type != BT_DATA_NAME_COMPLETE) {
        return true;  // Continue processing.
    }
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
    LOG_DBG("Found device %s rssi %d", buf, rssi);
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
    {
        int err = bt_conn_set_security(conn, BT_SECURITY_L4);
        if (err) {
            LOG_ERR("err %d: Failed to request security.", err);
            return;
        }
    }
    run_connected_callback(conn);
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
}

static void recycled() {
    start_scan();
}

static void identity_resolved(struct bt_conn *conn, const bt_addr_le_t *rpa,
                              const bt_addr_le_t *identity) {
    // TODO: remove excessive debug.
    char addr[BT_ADDR_LE_STR_LEN];
    bt_addr_le_to_str(rpa, addr, sizeof(addr));
    LOG_INF("Idneity-resolved. From: %s", addr);
    bt_addr_le_to_str(identity, addr, sizeof(addr));
    LOG_INF("To: %s", addr);
}

static void security_changed(struct bt_conn *conn, bt_security_t level,
                             enum bt_security_err err) {
    // TODO: remove excessive debug.
    LOG_INF("Sec changed: level %d err %d", (int)level, (int)err);
}

static struct bt_conn_cb m_conn_cb = {
    .connected = &connected,
    .disconnected = &disconnected,
    .recycled = &recycled,
    .identity_resolved = &identity_resolved,
    .security_changed = &security_changed,
};

static void passkey_display(struct bt_conn *conn, unsigned int passkey) {
    LOG_INF("Passkey display: %.6u", passkey);
    // TODO: alternative means to display.
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

static void passkey_entry(struct bt_conn* conn) {
    for (;;) {
        LOG_INF("Input passkey needed. 6 Digits:");
        char* s = console_getline();
        int32_t passkey = parse_6digit_number(s);
        if (passkey == -1) LOG_ERR("Invalid passkey. Retry.");
        int err = bt_conn_auth_passkey_entry(conn, passkey);
        if (err == 0) return;
        LOG_ERR("err %d: Failed to enter passkey.", err);
    }
}

static void passkey_confirm(struct bt_conn *conn, unsigned int passkey) {
    LOG_INF("Confirm [y/n]? Passkey: %.6u", passkey);
    for (;;) {
        char* s = console_getline();
        if (s[0] == 'y') {
            int err = bt_conn_auth_passkey_confirm(conn);
            if (err) LOG_ERR("err %d: Failed to confirm passkey.", err);
            return;
        } else if (s[0] == 'n') {
            int err = bt_conn_auth_cancel(conn);
            if (err) LOG_ERR("err %d: Failed to reject passkey.", err);
            return;
        }
    }

}

static void auth_cancel(struct bt_conn* conn) {
    // Do nothing.
}

// Both display and keyboard. Note that `.passkey_confirm` somehow must
// also be supplied when `.passkey_entry` is supplied, because depending
// on the peer capability, it might be just confirming a passkey correct
// or need to fully type the passkey.
static struct bt_conn_auth_cb m_conn_auth_cb = {
    .passkey_display = &passkey_display,
    .passkey_entry = &passkey_entry,
    .passkey_confirm = &passkey_confirm,
    .cancel = &auth_cancel,  // Required.
};

void pairing_complete(struct bt_conn *conn, bool bonded) {
    // TODO: remove excessive debug.
    LOG_INF("Paired. bonded=%d", (int)bonded);
}

void pairing_failed(struct bt_conn *conn, enum bt_security_err reason) {
    LOG_WRN("reason %d: Pairing failed.", (int)reason);
    (void)bt_conn_disconnect(conn, BT_HCI_ERR_AUTH_FAIL);
}

static struct bt_conn_auth_info_cb m_conn_auth_info_cb = {
    .pairing_complete = &pairing_complete,
    .pairing_failed = &pairing_failed,
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
    err = bt_conn_auth_cb_register(&m_conn_auth_cb);
    if (err) {
        LOG_ERR("err %d: Failed bt_conn_auth_cb_register().", err);
        return;
    }
    err = bt_conn_auth_info_cb_register(&m_conn_auth_info_cb);
    if (err) {
        LOG_ERR("err %d: Failed bt_conn_auth_info_cb_register().", err);
        return;
    }
    start_scan();
}
