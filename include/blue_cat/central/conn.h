// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#ifndef BLUE_CAT__INCLUDE__CENTRAL__CONN_H_
#define BLUE_CAT__INCLUDE__CENTRAL__CONN_H_

#include <zephyr/bluetooth/conn.h>

struct blue_cat_central_conn_loop_cb {
    // Peer device name as a preliminary filtering condition.
    const char* peer_name;
    // Called when a connection is successful.
    void (*connected)(struct bt_conn* conn);
    // Called for notification when disconnected.
    void (*disconnected)();
    // Asks for a passkey from 000000 to 999999. Anything outside the
    // value is regarded as aborted.
    int (*passkey_entry)();
    // Asks for a yes/no (true/false) whether `passkey` is correct.
    bool (*passkey_confirm)(int passkey);
};

// CALL ONLY ONCE: starts the BLE scan-connect-auth-disconnect-scan loop.
// Returns a non-zero error if `cb` or some config is wrong.
// `cb` must be alive for the whole lifespan of the program.
int blue_cat_central_conn_loop_kickoff(
        struct blue_cat_central_conn_loop_cb* cb);

#endif  // BLUE_CAT__INCLUDE__CENTRAL__CONN_H_
