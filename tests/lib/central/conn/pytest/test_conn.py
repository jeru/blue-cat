# Copyright 2024 Cheng Sheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
import bumbled_zephyr
from remote_device import create_remote_device


_PORT = 23458


@pytest.fixture
def link() -> LocalLink: return LocalLink()


@pytest.fixture
def bumbled_device(link) -> BumbledDevice:
    return bumbled_zephyr.create_bumbled_device_for_zephyr(
            'DUT', _PORT, link,
            bumbled_zephyr.find_zephyr_binary_from_env())


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


def test_connected_bonded(bumbled_device, link):
    async def run():
        async with bumbled_device:
            proc = bumbled_device.process
            remote = create_remote_device(link, name='TestPeerName')
            await remote.power_on()
            await remote.start_advertising()
            await _wait_until_line_with(
                proc.stdout,
                lambda line:
                    True if line.find('bt_conn_loop: Paired. bonded=1') != -1 else
                    None)
    asyncio.run(run())


def test_connected_peer_no_input(bumbled_device, link):
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
        async with bumbled_device:
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


def test_wrong_name(bumbled_device, link):
    async def run():
        async with bumbled_device:
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


def test_insecure_peer(bumbled_device, link):
    class NoPairingDelegate(PairingDelegate):
        async def accept(self): return False
    async def run():
        async with bumbled_device:
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
