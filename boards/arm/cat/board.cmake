# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

# WARNING: Do not add complex configures here. They should go into
#`support/openocd.cfg`, which is also consumed by the `west view-swo` extension
# command in this project.

board_runner_args(openocd --config
	"${CMAKE_CURRENT_LIST_DIR}/support/openocd.cfg")
include(${ZEPHYR_BASE}/boards/common/openocd.board.cmake)
