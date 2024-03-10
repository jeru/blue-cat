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
import struct
from typing import Callable
import sys
from unittest.mock import patch

import bumble
from bumble.device import Connection, Device, Peer
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
import bumbled_zephyr
from central_device import CentralDevice


_PORT = 23456
# TODO: dedup constants.
_UUID_DOORBELL_SERVICE = '7E9648B5-EE32-4B37-9B96-1C5904381BE2'
_UUID_DOORBELL_CHARACTERISTIC = '8AE241C9-8029-4051-890D-071F62C36FE3'


@pytest.fixture
def link() -> LocalLink: return LocalLink()


@pytest.fixture
def bumbled_device(link) -> BumbledDevice:
    logging.debug('Created a BumbledDevice')
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


@pytest.mark.asyncio
async def test_discoverd_and_subscribed(bumbled_device, link):
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
            mock_get_number.return_value = 321098  # Fixed on DUT.
            await asyncio.wait_for(conn.pair(), timeout=10.0)
        mock_get_number.assert_awaited_once()
        assert conn.is_encrypted

        peer = Peer(conn)
        [service] = await peer.discover_service(
                uuid=_UUID_DOORBELL_SERVICE)
        [characteristic] = await service.discover_characteristics()
        assert characteristic.uuid == _UUID_DOORBELL_CHARACTERISTIC

        queue = asyncio.Queue()
        def notify_cb(value: bytes):
            i = struct.unpack('i', value)[0]
            queue.put_nowait(i)
        await characteristic.subscribe(notify_cb)
        logging.debug('Subscribed.')

        values = [await queue.get() for _ in range(2)]
        # 123 and 456 are the alternating values to this characteristic,
        # defined in DUT.
        assert values == [123, 456] or values == [456, 123], (
                f'values = {str(values)}')
        read_task.cancel()


@pytest.mark.asyncio
async def test_delay_passkey(bumbled_device, link):
    async with bumbled_device:
        proc = bumbled_device.process
        read_task = read_and_print(proc.stdout)

        tester_device = CentralDevice('Peer', link)
        await tester_device.power_on()
        conn = await tester_device.scan_and_connect(
                wait_for_security_request=False)

        # Block pairing by this, we don't provide it a value.
        number = asyncio.Future()
        with patch('bumble.pairing.PairingDelegate.get_number'
                   ) as mock_get_number:
            mock_get_number.side_effect = lambda: number

            peer = Peer(conn)
            [service] = await peer.discover_service(
                    uuid=_UUID_DOORBELL_SERVICE)
            [characteristic] = await service.discover_characteristics()
            assert characteristic.uuid == _UUID_DOORBELL_CHARACTERISTIC

            # Test: cannot subscribe.
            with pytest.raises(bumble.core.ProtocolError) as exc:
                await characteristic.subscribe()
            assert 'ATT_INSUFFICIENT_AUTHENTICATION_ERROR' in str(
                    str(exc.value))

            # Test: cannot read.
            with pytest.raises(bumble.core.ProtocolError) as exc:
                await characteristic.read_value()
            assert 'ATT_INSUFFICIENT_AUTHENTICATION_ERROR' in str(
                    str(exc.value))

        read_task.cancel()
