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

from bumble.device import Connection, Device
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
import bumbled_zephyr
from central_device import SmpCentralDevice


_PORT = 23457


@pytest.fixture
def link() -> LocalLink: return LocalLink()


@pytest.fixture
def bumbled_device(link) -> BumbledDevice:
    return bumbled_zephyr.create_bumbled_device_for_zephyr(
            'DUT', _PORT, link,
            bumbled_zephyr.find_zephyr_binary_from_env())


def test_connected_bonded(bumbled_device, link):
    async def run():
        async with bumbled_device:
            bumbled_device.controller.random_address = ':'.join(['A0'] * 6)
            proc = bumbled_device.process
            tester_device = SmpCentralDevice('Peer', link)
            await tester_device.power_on()
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
                        tester_device.put_passkey(int(line[p : q]))
                    elif line.find('Paired. bonded=1') != -1:
                        logging.debug('Done')
                        return True
            await asyncio.gather(read(), tester_device.connect_with_pairing())
    asyncio.run(run())
