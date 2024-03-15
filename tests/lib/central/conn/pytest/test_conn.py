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
from unittest.mock import patch

from bumble.device import Device
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

from bluet.process import BumbledProcess
from bluet.process_zephyr import create_bumbled_process_for_zephyr
from bluet.peripheral import advertise_until_connected
from bluet.tester_device import create_tester_device


_PORT = 23458
_BONDED_MESSAGE = "bt_conn_loop: Paired. bonded=1"
_WRONG_PEER_NAME_MESSAGE = "bt_conn_loop: device_found: Peer name wrong."


@pytest.fixture
def link() -> LocalLink:
    return LocalLink()


@pytest.fixture
async def bumbled_process(link) -> BumbledProcess:
    return create_bumbled_process_for_zephyr("DUT", port=_PORT, link=link)


@pytest.fixture(name="tester_device")
async def fixture_tester_device(link) -> Device:
    device = create_tester_device("TestPeerName", link)
    await device.power_on()
    return device


@pytest.mark.asyncio
async def test_connected_bonded(bumbled_process, tester_device):
    async with bumbled_process:
        succ = asyncio.Future()

        def process_line(line: str):
            if line.find(_BONDED_MESSAGE) != -1:
                succ.set_result(True)

        bumbled_process.start_monitoring_stdout(process_line)

        await advertise_until_connected(tester_device)
        await succ


@pytest.mark.asyncio
async def test_connected_peer_no_input(bumbled_process, link):
    tester_device = create_tester_device(
        name="TestPeerName",
        link=link,
        io_capability=PairingDelegate.DISPLAY_OUTPUT_ONLY,
    )
    await tester_device.power_on()

    async with bumbled_process:
        succ = asyncio.Future()

        def process_line(line: str):
            if line.find(_BONDED_MESSAGE) != -1:
                succ.set_result(True)

        bumbled_process.start_monitoring_stdout(process_line)
        proc = bumbled_process.process

        async def display_number(number: int, digits: int) -> None:
            line = "PK%.*dPK\n" % (digits, number)
            proc.stdin.write(line.encode("utf-8"))
            await proc.stdin.drain()

        with patch(
            "bumble.pairing.PairingDelegate.display_number", side_effect=display_number
        ):
            await advertise_until_connected(tester_device)
            await succ


@pytest.mark.asyncio
async def test_wrong_name(bumbled_process, link):
    tester_device = create_tester_device(name="WRONG_TestPeerName", link=link)
    await tester_device.power_on()

    async with bumbled_process:
        succ = asyncio.Future()

        def process_line(line: str):
            if line.find(_WRONG_PEER_NAME_MESSAGE) != -1:
                succ.set_result(True)
            elif line.find(_BONDED_MESSAGE) != -1:
                succ.set_result(False)

        bumbled_process.start_monitoring_stdout(process_line)

        await tester_device.start_advertising()
        result = await succ
        assert result


@pytest.mark.asyncio
async def test_insecure_peer(bumbled_process, tester_device):
    async with bumbled_process:
        succ = asyncio.Future()

        def process_line(line: str):
            # Reason 5: BT_HCI_ERR_AUTH_FAIL
            if line.find("bt_conn_loop: reason 5: Disconnected.") != -1:
                succ.set_result(True)
            elif line.find(_BONDED_MESSAGE) != -1:
                succ.set_result(False)

        bumbled_process.start_monitoring_stdout(process_line)

        with patch(
            "bumble.pairing.PairingDelegate.accept", return_value=False
        ) as mock_accept:
            await advertise_until_connected(tester_device)
            result = await succ
        mock_accept.assert_awaited_once()
        assert result
