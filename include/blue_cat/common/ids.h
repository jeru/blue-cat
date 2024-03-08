// Copyright 2024 Cheng Sheng
// SPDX-License-Identifier: Apache-2.0

#ifndef BLUE_CAT__INCLUDE__COMMON__IDS_H_
#define BLUE_CAT__INCLUDE__COMMON__IDS_H_

#include <zephyr/bluetooth/uuid.h>

#define BLUE_CAT_PERIPHERAL_DEVICE_NAME "BlueCat"

// Primary service.
#define BT_UUID_BLUE_CAT_DOORBELL_SERVICE \
    BT_UUID_DECLARE_128(BT_UUID_128_ENCODE( \
        0x7E9648B5, 0xEE32, 0x4B37, 0x9B96, 0x1C5904381BE2))

// GATT characteristic. Notifiable. AUTH required.
#define BT_UUID_BLUE_CAT_DOORBELL_RING \
    BT_UUID_DECLARE_128(BT_UUID_128_ENCODE( \
        0x8AE241C9, 0x8029, 0x4051, 0x890D, 0x071F62C36FE3))

#endif  // BLUE_CAT__INCLUDE__COMMON__IDS_H_
