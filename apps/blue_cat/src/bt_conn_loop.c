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
    // TODO: Implement connection accept list.
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
    {
        int err = bt_conn_set_security(conn, BT_SECURITY_L4);
        if (err) {
            LOG_ERR("err %d: Failed to request security.", err);
            return;
        }
    }

    void (*user_connected)(struct bt_conn* conn) =
        atomic_ptr_get(&m_user_conn_cb);
    if (user_connected) user_connected(conn);
}

static void disconnected(struct bt_conn* conn, uint8_t reason) {
    LOG_INF("reason %d: Disconnected.", reason);
}

static void recycled() {
    start_advertising();
}

static bool le_param_req(struct bt_conn *conn,
                         struct bt_le_conn_param *param) {
    return true;  // TODO: ensure `param` not bad for the battery.
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
    .le_param_req = &le_param_req,
    .identity_resolved = &identity_resolved,
    .security_changed = &security_changed,
};

static void passkey_display(struct bt_conn *conn, unsigned int passkey) {
    LOG_INF("Passkey display: %.6u", passkey);
    // TODO: implement Morse code display via LED, so pairing doesn't depend
    // on debugging output.
}

static void auth_cancel(struct bt_conn *conn) {
    // Do nothing.
}

// The existence of the provided functions here is the source of truth for
// Zephyr to determine whether the device has the ability to display, input,
// confirm yes no, etc., for the purpose of bluetooth pairing. Here:
// display-only.
static struct bt_conn_auth_cb m_conn_auth_cb = {
    .passkey_display = &passkey_display,
    .passkey_entry = NULL,  // Explicit null: no input means.
    .cancel = auth_cancel,  // Required.
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

void blue_cat_bt_conn_loop_start() {
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

    start_advertising();
}

