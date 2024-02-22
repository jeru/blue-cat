#!/bin/bash
#
# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0
#
# Intended usage:
#     $ source ~/zephyrproject/.venv/bin/activate
#     $ source extra-env.sh

if ! echo "$VIRTUAL_ENV" | grep zephyr; then
	echo "No \$VIRTUAL_ENV or it is not a zephyr one."
	return 1
fi

export ZEPHYR_BASE="$(dirname "$VIRTUAL_ENV")/zephyr"
export BOARD_ROOT="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

echo "DONE"
