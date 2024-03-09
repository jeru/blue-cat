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

#ifndef BLUE_CAT__INCLUDE__PERIPHERAL__GATT_DOORBELL_H_
#define BLUE_CAT__INCLUDE__PERIPHERAL__GATT_DOORBELL_H_

// Updates the BLE characteristic to `duration_ms`. When the value is different
// from the previous one, subscribed clients will be notified.
void blue_cat_gatt_doorbell_ring_write(int32_t duration_ms);

#endif  // BLUE_CAT__INCLUDE__PERIPHERAL__GATT_DOORBELL_H_
