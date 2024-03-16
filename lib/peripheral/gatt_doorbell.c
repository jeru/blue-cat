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

#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>
LOG_MODULE_REGISTER(doorbell);

#include <blue_cat/common/ids.h>
#include <blue_cat/peripheral/gatt_doorbell.h>

// int32
static atomic_t m_doorbell_ring = ATOMIC_INIT(-1);

static ssize_t read_doorbell_ring(struct bt_conn *conn,
                                  const struct bt_gatt_attr *attr, void *buf,
                                  uint16_t len, uint16_t offset) {
    int32_t ring = atomic_get(&m_doorbell_ring);
    return bt_gatt_attr_read(conn, attr, buf, len, offset, &ring, sizeof(ring));
}

static void doorbell_ring_ccc_changed(struct bt_gatt_attr const *attr,
                                      uint16_t value) {
    // Do nothing.
}

// The characteristic presentation format of the doorbell ring.
// Format constants see
// https://www.bluetooth.com/specifications/assigned-numbers/ PDF Sec 2.4
// characteristic presentation format.
static const struct bt_gatt_cpf ring_cpf = {
    .format = 0x10,  // int32
};

BT_GATT_SERVICE_DEFINE(
    doorbell_service,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_BLUE_CAT_DOORBELL_SERVICE),
    BT_GATT_CHARACTERISTIC(BT_UUID_BLUE_CAT_DOORBELL_RING,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ_AUTHEN, &read_doorbell_ring, NULL,
                           NULL),
    BT_GATT_CCC(doorbell_ring_ccc_changed,
                BT_GATT_PERM_READ_AUTHEN | BT_GATT_PERM_WRITE_AUTHEN),
    BT_GATT_CPF(&ring_cpf),
    BT_GATT_CUD("DoorbellRing in ms. -1 for not ongoing.",
                BT_GATT_PERM_READ_AUTHEN));

void blue_cat_gatt_doorbell_ring_write(int32_t duration_ms) {
    int32_t old_value = atomic_set(&m_doorbell_ring, (atomic_val_t)duration_ms);
    if (old_value == duration_ms) {
        return;
    }
    int err = bt_gatt_notify(/*conn=*/NULL, &doorbell_service.attrs[1],
                             &duration_ms, sizeof(duration_ms));
    if (err && err != -ENOTCONN) {
        LOG_ERR("err %d: Failed to notify.", err);
    }
}
