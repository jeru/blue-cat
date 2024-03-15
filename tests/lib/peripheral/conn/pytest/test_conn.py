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
import re
from unittest.mock import patch

from bumble.device import Device
from bumble.link import LocalLink
import pytest

from bluet.process import BumbledProcess
from bluet.process_zephyr import create_bumbled_process_for_zephyr
from bluet.central import scan_and_connect
from bluet.tester_device import create_tester_device


_PORT = 23457


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
async def test_connected_bonded(bumbled_process, tester_device):
    async with bumbled_process:
        # Served by `read_task` via `proc.stdout` and consumed by pairing.
        passkey_fut = asyncio.Future()

        def process_line(line: str):
            match = re.search(r"PK<(?P<key>\d+)>", line)
            if match:
                passkey_fut.set_result(int(match["key"]))

        bumbled_process.start_monitoring_stdout(process_line)

        async def read_passkey():
            return await passkey_fut

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        with patch(
            "bumble.pairing.PairingDelegate.get_number", side_effect=read_passkey
        ) as mock_get_number:
            await asyncio.wait_for(conn.pair(), timeout=10.0)
        mock_get_number.assert_awaited_once()


@pytest.mark.asyncio
async def test_wrong_passkey(bumbled_process, tester_device):
    async with bumbled_process:
        bumbled_process.start_monitoring_stdout()

        conn, auth_req_fut = await scan_and_connect(tester_device)
        await auth_req_fut
        # DUT has hardcoded a different passkey than 999999.
        with patch(
            "bumble.pairing.PairingDelegate.get_number", return_value=999999
        ) as mock_get_number:
            with pytest.raises(asyncio.CancelledError) as err:
                await asyncio.wait_for(conn.pair(), timeout=10.0)
            assert "disconnection event occurred" in str(
                err.value
            ), f"Mismatch. Actual: {str(err.value)}"
        mock_get_number.assert_awaited_once()
        assert not conn.is_encrypted
