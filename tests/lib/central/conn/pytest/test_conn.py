# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from pathlib import Path
from typing import Callable
import sys

from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
from bumbled_zephyr import create_bumbled_device_for_zephyr
from remote_device import create_remote_device


_BUILD_DIR_ARG_PREFIX = '--build-dir'
_PORT = 23456


def _find_build_dir() -> str:
    for i, arg in enumerate(sys.argv):
        if arg.startswith(_BUILD_DIR_ARG_PREFIX):
            arg = arg[len(_BUILD_DIR_ARG_PREFIX):]
            if not arg:
                return sys.argv[i + 1]
            if arg[0] == '=':
                return arg[1:]
    raise RuntimeError(f'Cannot find flag: {_BUILD_DIR_ARG_PREFIX}')


async def _wait_until_line_with(
        s: asyncio.StreamReader,
        w: Callable[str, bool | None]) -> None:
    while True:
        line = await s.readline()
        if not line: break
        line = line.decode('utf-8')
        logging.debug('-----STDOUT----- %s', line)
        value = w(line)
        if value is not None: return value


@pytest.fixture(name='bumbler')
def fixture_bumbler() -> Callable[LocalLink, BumbledDevice]:
    bin_path = Path(_find_build_dir()) / 'zephyr/zephyr.exe'
    assert bin_path.exists()
    def create(link: LocalLink) -> BumbledDevice:
        return create_bumbled_device_for_zephyr(
            'DUT', _PORT, link, str(bin_path), extra_program_args=[])
    return create


def test_connected_bonded(bumbler):
    async def run():
        link = LocalLink()
        async with bumbler(link) as bumbled_device:
            proc = bumbled_device.process
            remote = create_remote_device(
                link, name='TestPeerName')
            await remote.power_on()
            await remote.start_advertising()
            await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    True if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
    asyncio.run(run())


def test_connected_peer_no_input(bumbler):
    # DUT has display and keyboard. So authentication will be the peer
    # displaying the passkey and DUT fully inputs.
    class DisplayDelegate(PairingDelegate):
        def __init__(self, proc_stdin):
            super().__init__(io_capability=PairingDelegate.DISPLAY_OUTPUT_ONLY)
            self.proc_stdin = proc_stdin

        async def display_number(self, number: int, digits: int) -> None:
            line = 'PK%.*dPK\n' % (digits, number)
            self.proc_stdin.write(line.encode('utf-8'))
            await self.proc_stdin.drain()

    async def run():
        link = LocalLink()
        async with bumbler(link) as bumbled_device:
            proc = bumbled_device.process
            remote = create_remote_device(
                link, name='TestPeerName',
                delegate=DisplayDelegate(proc.stdin))
            await remote.power_on()
            await remote.start_advertising()
            await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    True if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
    asyncio.run(run())


def test_wrong_name(bumbler):
    async def run():
        link = LocalLink()
        async with bumbler(link) as bumbled_device:
            proc = bumbled_device.process
            remote = create_remote_device(
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


def test_insecure_peer(bumbler):
    class NoPairingDelegate(PairingDelegate):
        async def accept(self): return False
    async def run():
        link = LocalLink()
        async with bumbler(link) as bumbled_device:
            proc = bumbled_device.process
            remote = create_remote_device(
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
