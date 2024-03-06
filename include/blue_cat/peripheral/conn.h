// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#ifndef BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_
#define BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_

#include <zephyr/bluetooth/conn.h>

struct blue_cat_peripheral_conn_loop_cb {
    // Peer device name as a preliminary filtering condition.
    const char* peer_name;
    // Called when a connection is successful.
    void (*connected)(struct bt_conn* conn);
    // Called for notification when disconnected.
    void (*disconnected)();
    // Called to display `passkey`.
    void (*passkey_display)(int passkey);
};

// CALL ONLY ONCE: starts the BLE adv-connect-auth-disconnect-adv loop.
// Returns a non-zero error if `cb` or some config is wrong.
// `cb` must be alive for the whole lifespan of the program.
//
// The device assumes the ability to display only.
int blue_cat_peripheral_conn_loop_kickoff(
        struct blue_cat_peripheral_conn_loop_cb* cb);

#endif  // BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_
