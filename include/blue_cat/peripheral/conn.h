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

#ifndef BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_
#define BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_

#include <zephyr/bluetooth/conn.h>

struct blue_cat_peripheral_conn_loop_cb {
    // Peer device name as a preliminary filtering condition.
    const char *peer_name;
    // Called when a connection is successful.
    void (*connected)(struct bt_conn *conn);
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
    struct blue_cat_peripheral_conn_loop_cb *cb);

#endif  // BLUE_CAT__INCLUDE__PERIPHERAL__CONN_H_
