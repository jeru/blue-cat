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
import re
import sys
from typing import Callable
from unittest.mock import patch

from bumble.device import Connection, Device
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
import bumbled_zephyr
from bumbled_helpers import read_and_print
from central_device import scan_and_connect
from tester_device import create_tester_device


_PORT = 23457


@pytest.fixture
def link() -> LocalLink: return LocalLink()


@pytest.fixture
async def bumbled_device(link) -> BumbledDevice:
    return bumbled_zephyr.create_bumbled_device_for_zephyr(
            'DUT', _PORT, link,
            bumbled_zephyr.find_zephyr_binary_from_env())


@pytest.fixture(name='tester_device')
async def fixture_tester_device(link) -> Device:
    device = create_tester_device('Peer', link)
    await device.power_on()
    return device


@pytest.mark.asyncio
async def test_connected_bonded(bumbled_device, tester_device):
    async with bumbled_device:
        proc = bumbled_device.process
        # Served by `read_task` via `proc.stdout` and consumed by pairing.
        passkey_fut = asyncio.Future()

        def process_line(line: str):
            match = re.search(r'PK<(?P<key>\d+)>', line)
            if match:
                passkey_fut.set_result(int(match['key']))
        read_task = read_and_print(proc.stdout, process_line)

        async def read_passkey():
            return await passkey_fut

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        with patch('bumble.pairing.PairingDelegate.get_number',
                   side_effect=read_passkey) as mock_get_number:
            await asyncio.wait_for(conn.pair(), timeout=10.0)
        mock_get_number.assert_awaited_once()

        read_task.cancel()


@pytest.mark.asyncio
async def test_wrong_passkey(bumbled_device, tester_device):
    async with bumbled_device:
        proc = bumbled_device.process
        read_task = read_and_print(proc.stdout)

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        # DUT has hardcoded a different passkey than 999999.
        with patch('bumble.pairing.PairingDelegate.get_number',
                   return_value = 999999) as mock_get_number:
            with pytest.raises(asyncio.CancelledError) as err:
                await asyncio.wait_for(conn.pair(), timeout=10.0)
            assert "disconnection event occurred" in str(err.value), (
                    f'Mismatch. Actual: {str(err.value)}')
        mock_get_number.assert_awaited_once()
        assert not conn.is_encrypted
        read_task.cancel()
