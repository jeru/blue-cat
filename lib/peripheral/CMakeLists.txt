# SPDX-License-Identifier: Apache-2.0

zephyr_library()
zephyr_library_sources_ifdef(CONFIG_BLUE_CAT_PERIPHERAL_CONN conn.c)
zephyr_library_sources_ifdef(CONFIG_BLUE_CAT_PERIPHERAL_DOORBELL doorbell.c)
