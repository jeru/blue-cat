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
import struct
from unittest.mock import patch

import bumble
from bumble.device import Device, Peer
from bumble.link import LocalLink
import pytest

from bluet.process import BumbledProcess
from bluet.process_zephyr import create_bumbled_process_for_zephyr
from bluet.central import scan_and_connect
from bluet.tester_device import create_tester_device


_PORT = 23456
# TODO: dedup constants.
_UUID_DOORBELL_SERVICE = "7E9648B5-EE32-4B37-9B96-1C5904381BE2"
_UUID_DOORBELL_CHARACTERISTIC = "8AE241C9-8029-4051-890D-071F62C36FE3"


@pytest.fixture
def link() -> LocalLink:
    return LocalLink()


@pytest.fixture
async def bumbled_process(link) -> BumbledProcess:
    return create_bumbled_process_for_zephyr("DUT", port=_PORT, link=link)


@pytest.fixture(name="tester_device")
async def fixture_tester_device(link) -> Device:
    device = create_tester_device("Peer", link)
    await device.power_on()
    return device


@pytest.mark.asyncio
async def test_discoverd_and_subscribed(bumbled_process, tester_device):
    async with bumbled_process:
        bumbled_process.controller.random_address = ":".join(["A0"] * 6)
        bumbled_process.start_monitoring_stdout()

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        with patch("bumble.pairing.PairingDelegate.get_number") as mock_get_number:
            mock_get_number.return_value = 321098  # Fixed on DUT.
            await asyncio.wait_for(conn.pair(), timeout=10.0)
        mock_get_number.assert_awaited_once()
        assert conn.is_encrypted

        peer = Peer(conn)
        [service] = await peer.discover_service(uuid=_UUID_DOORBELL_SERVICE)
        [characteristic] = await service.discover_characteristics()
        assert characteristic.uuid == _UUID_DOORBELL_CHARACTERISTIC

        queue = asyncio.Queue()

        def notify_cb(value: bytes):
            i = struct.unpack("i", value)[0]
            queue.put_nowait(i)

        await characteristic.subscribe(notify_cb)
        logging.debug("Subscribed.")

        values = [await queue.get() for _ in range(2)]
        # 123 and 456 are the alternating values to this characteristic,
        # defined in DUT.
        assert values == [123, 456] or values == [456, 123], f"values = {str(values)}"


@pytest.mark.asyncio
async def test_delay_passkey(bumbled_process, tester_device):
    async with bumbled_process:
        bumbled_process.start_monitoring_stdout()

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        # Block pairing by this, we don't provide it a value.
        number = asyncio.Future()

        async def get_number():
            return await number

        with patch("bumble.pairing.PairingDelegate.get_number", side_effect=get_number):
            peer = Peer(conn)
            [service] = await peer.discover_service(uuid=_UUID_DOORBELL_SERVICE)
            [characteristic] = await service.discover_characteristics()
            assert characteristic.uuid == _UUID_DOORBELL_CHARACTERISTIC

            # Test: cannot subscribe.
            with pytest.raises(bumble.core.ProtocolError) as exc:
                await characteristic.subscribe()
            assert "ATT_INSUFFICIENT_AUTHENTICATION_ERROR" in str(str(exc.value))

            # Test: cannot read.
            with pytest.raises(bumble.core.ProtocolError) as exc:
                await characteristic.read_value()
            assert "ATT_INSUFFICIENT_AUTHENTICATION_ERROR" in str(str(exc.value))
