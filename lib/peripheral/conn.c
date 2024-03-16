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

// The part of the callback hell that keeps the adv-connect-disconnect loop.

#include <blue_cat/peripheral/conn.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
LOG_MODULE_REGISTER(bt_conn_loop, CONFIG_BLUE_CAT_PERIPHERAL_CONN_LOG_LEVEL);

#if CONFIG_BT_MAX_CONN != 1
#error "Expect CONFIG_BT_MAX_CONN == 1"
#endif

static const struct bt_data m_adv_data[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_SOME, BT_UUID_16_ENCODE(BT_UUID_BAS_VAL)),
};

static void start_advertising() {
    // TODO: Implement connection accept list.
    int err = bt_le_adv_start(BT_LE_ADV_CONN_NAME_AD, m_adv_data,
                              ARRAY_SIZE(m_adv_data),
                              /*sd=*/NULL, /*sd_len=*/0);
    if (err) {
        LOG_ERR("err %d: Failed to start adv.", err);
    }
}

static void stop_advertising() {
    int err = bt_le_adv_stop();
    if (err) {
        LOG_ERR("err %d: Failed to stop adv.", err);
    }
}

static struct blue_cat_peripheral_conn_loop_cb *m_loop_cb = NULL;

static void connected(struct bt_conn *conn, uint8_t err) {
    if (err) {
        LOG_WRN("err %d: Failed connection.", err);
        return;
    }
    stop_advertising();
    {
        int err = bt_conn_set_security(conn, BT_SECURITY_L4);
        if (err) {
            LOG_ERR("err %d: Failed to request security.", err);
            (void)bt_conn_disconnect(conn, BT_HCI_ERR_AUTH_FAIL);
            return;
        }
    }
    LOG_DBG("Connected.");
    if (m_loop_cb->connected != NULL) {
        m_loop_cb->connected(conn);
    }
}

static void disconnected(struct bt_conn *conn, uint8_t reason) {
    LOG_DBG("reason %d: Disconnected.", reason);
    if (m_loop_cb->disconnected != NULL) {
        m_loop_cb->disconnected(conn);
    }
}

static void recycled() { start_advertising(); }

static bool le_param_req(struct bt_conn *conn, struct bt_le_conn_param *param) {
    LOG_DBG("received new conn param.");
    return true;  // TODO: ensure `param` not bad for the battery.
}

static void identity_resolved(struct bt_conn *conn, const bt_addr_le_t *rpa,
                              const bt_addr_le_t *identity) {
    char addr[BT_ADDR_LE_STR_LEN];
    bt_addr_le_to_str(rpa, addr, sizeof(addr));
    LOG_DBG("Idneity-resolved. From: %s", addr);
    bt_addr_le_to_str(identity, addr, sizeof(addr));
    LOG_DBG("To: %s", addr);
}

static void security_changed(struct bt_conn *conn, bt_security_t level,
                             enum bt_security_err err) {
    LOG_DBG("Sec changed: level %d err %d", (int)level, (int)err);
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
    m_loop_cb->passkey_display(passkey);
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
    .passkey_entry = NULL,   // Explicit null: no input means.
    .cancel = &auth_cancel,  // Required.
};

void pairing_complete(struct bt_conn *conn, bool bonded) {
    LOG_DBG("Paired. bonded=%d", (int)bonded);
}

void pairing_failed(struct bt_conn *conn, enum bt_security_err reason) {
    LOG_WRN("reason %d: Pairing failed.", (int)reason);
    int err = bt_conn_disconnect(conn, BT_HCI_ERR_AUTH_FAIL);
    if (err) {
        LOG_ERR("err %d: Failed to disconnect.", err);
    }
}

static struct bt_conn_auth_info_cb m_conn_auth_info_cb = {
    .pairing_complete = &pairing_complete,
    .pairing_failed = &pairing_failed,
};

static atomic_t m_inited = ATOMIC_INIT(0);

int blue_cat_peripheral_conn_loop_kickoff(
    struct blue_cat_peripheral_conn_loop_cb *cb) {
    if (cb == NULL || cb->peer_name == NULL || cb->passkey_display == NULL) {
        return -EINVAL;
    }
    if (!atomic_cas(&m_inited, 0, 1)) {
        return -EALREADY;
    }
    m_loop_cb = cb;
    int err;

    err = bt_enable(/*cb=*/NULL);
    if (err) {
        LOG_ERR("err %d: Failed bt_enable().", err);
        return err;
    }
    bt_conn_cb_register(&m_conn_cb);
    err = bt_conn_auth_cb_register(&m_conn_auth_cb);
    if (err) {
        LOG_ERR("err %d: Failed bt_conn_auth_cb_register().", err);
        return err;
    }
    err = bt_conn_auth_info_cb_register(&m_conn_auth_info_cb);
    if (err) {
        LOG_ERR("err %d: Failed bt_conn_auth_info_cb_register().", err);
        return err;
    }

    start_advertising();
    return 0;
}
