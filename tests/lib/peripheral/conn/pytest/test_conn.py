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
from unittest.mock import patch

from bumble.device import Connection, Device
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
import bumbled_zephyr
from central_device import CentralDevice


_PORT = 23457


@pytest.fixture
def link() -> LocalLink: return LocalLink()


@pytest.fixture
def bumbled_device(link) -> BumbledDevice:
    return bumbled_zephyr.create_bumbled_device_for_zephyr(
            'DUT', _PORT, link,
            bumbled_zephyr.find_zephyr_binary_from_env())


def read_and_print(stdout: asyncio.StreamReader) -> asyncio.Task:
    async def read():
        while True:
            line = await stdout.readline()
            if not line: break
            line = line.decode('utf-8')
            logging.debug('-----STDOUT----- %s', line)
    return asyncio.create_task(read())


def test_connected_bonded(bumbled_device, link):
    async def run():
        async with bumbled_device:
            bumbled_device.controller.random_address = ':'.join(['A0'] * 6)
            proc = bumbled_device.process
            tester_device = CentralDevice('Peer', link)
            await tester_device.power_on()

            # `read()` will get the passkey and enqueue. `connect()` will consume it.
            passkey_queue = asyncio.Queue(1)
            async def read():
                while True:
                    line = await proc.stdout.readline()
                    if not line: break
                    line = line.decode('utf-8')
                    logging.debug('-----STDOUT----- %s', line)
                    p = line.find('PK<')
                    if p != -1:
                        p = p + 3
                        q = line.find('>', p)
                        passkey_queue.put_nowait(int(line[p : q]))
                    elif line.find('Paired. bonded=1') != -1:
                        logging.debug('Done')
                        return True
            async def connect():
                conn = await tester_device.scan_and_connect(
                        wait_for_security_request=True)
                with patch('bumble.pairing.PairingDelegate.get_number'
                           ) as mock_get_number:
                    mock_get_number.side_effect = passkey_queue.get
                    await asyncio.wait_for(conn.pair(), timeout=10.0)
                mock_get_number.assert_awaited_once()

            await asyncio.gather(read(), connect())
    asyncio.run(run())


def test_wrong_passkey(bumbled_device, link):
    async def run():
        async with bumbled_device:
            bumbled_device.controller.random_address = ':'.join(['A0'] * 6)
            proc = bumbled_device.process
            read_task = read_and_print(proc.stdout)

            tester_device = CentralDevice('Peer', link)
            await tester_device.power_on()

            conn = await tester_device.scan_and_connect(
                    wait_for_security_request=True)
            with patch('bumble.pairing.PairingDelegate.get_number'
                       ) as mock_get_number:
                mock_get_number.return_value = 999999  # Wrong passkey
                with pytest.raises(asyncio.CancelledError) as err:
                    await asyncio.wait_for(conn.pair(), timeout=10.0)
                assert "disconnection event occurred" in str(err.value), (
                        f'Mismatch. Actual: {str(err.value)}')
            mock_get_number.assert_awaited_once()
            assert not conn.is_encrypted
            read_task.cancel()
    asyncio.run(run())
