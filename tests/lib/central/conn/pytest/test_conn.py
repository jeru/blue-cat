# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import os.path
from pathlib import Path
import pytest
import typing
import sys

from bumble.pairing import PairingDelegate
import bumbled_dut


_BUILD_DIR_ARG_PREFIX = '--build-dir'
_PORT = 23456


def _find_build_dir() -> str:
    for i, arg in enumerate(sys.argv):
        if arg.startswith(_BUILD_DIR_ARG_PREFIX):
            arg = arg[len(_BUILD_DIR_ARG_PREFIX):]
            if not arg:
                return sys.argv[i + 1]
            elif arg[0] == '=':
                return arg[1:]
    raise RuntimeError(f'Cannot find flag: {_BUILD_DIR_ARG_PREFIX}')


async def _wait_until_line_with(
        s: asyncio.StreamReader,
        w: typing.Callable[str, bool | None]) -> None:
    while True:
        line = await s.readline()
        line = line.decode('utf-8')
        logging.debug(line)
        value = w(line)
        if value is not None: return value


@pytest.fixture
def bin_runner() -> bumbled_dut.BumbledDut:
    return bumbled_dut.BumbledDut(_find_build_dir(), _PORT)


def test_connected_bonded(bin_runner):
    async def run():
        async with bin_runner as (proc, link):
            remote = bumbled_dut.create_remote_device(
                link, name='TestPeerName')
            await remote.power_on()
            await remote.start_advertising()
            await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    True if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
    asyncio.run(run())


def test_wrong_name(bin_runner):
    async def run():
        async with bin_runner as (proc, link):
            remote = bumbled_dut.create_remote_device(
                link, name='WRONG___PeerName')
            await remote.power_on()
            await remote.start_advertising()
            result = await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    True if line.find('bt_conn_loop: device_found: Peer name wrong.') == -1 else
                    False if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
            assert result
    asyncio.run(run())


def test_insecure_peer(bin_runner):
    class NoPairingDelegate(PairingDelegate):
        def accept(self): return False
    async def run():
        async with bin_runner as (proc, link):
            remote = bumbled_dut.create_remote_device(
                link, name='TestPeerName', delegate=NoPairingDelegate())
            await remote.power_on()
            await remote.start_advertising()
            await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    # Reason 5: BT_HCI_ERR_AUTH_FAIL
                    True if line.find('bt_conn_loop: reason 5: Disconnected.') != -1 else
                    False if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
    asyncio.run(run())
