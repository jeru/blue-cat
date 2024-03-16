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

#ifndef BLUE_CAT__INCLUDE__COMMON__IDS_H_
#define BLUE_CAT__INCLUDE__COMMON__IDS_H_

#include <zephyr/bluetooth/uuid.h>

#define BLUE_CAT_PERIPHERAL_DEVICE_NAME "BlueCat"

// Primary service.
#define BT_UUID_BLUE_CAT_DOORBELL_SERVICE                                      \
    BT_UUID_DECLARE_128(BT_UUID_128_ENCODE(0x7E9648B5, 0xEE32, 0x4B37, 0x9B96, \
                                           0x1C5904381BE2))

// GATT characteristic. Notifiable. AUTH required.
#define BT_UUID_BLUE_CAT_DOORBELL_RING                                         \
    BT_UUID_DECLARE_128(BT_UUID_128_ENCODE(0x8AE241C9, 0x8029, 0x4051, 0x890D, \
                                           0x071F62C36FE3))

#endif  // BLUE_CAT__INCLUDE__COMMON__IDS_H_
