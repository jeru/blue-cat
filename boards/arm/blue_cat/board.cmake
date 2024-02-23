# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

set(OPENOCD_NRF5_SUBFAMILY nrf52)
set(OPENOCD_NRF5_INTERFACE cmsis-dap)
include(${ZEPHYR_BASE}/boards/common/openocd-nrf5.board.cmake)
