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

from bumble.device import Connection, Device, Peer
from bumble.link import LocalLink
from bumble.pairing import PairingDelegate
import pytest

# TODO: Remove after the testing helpers are made a library.
sys.path.append(str(Path(__file__).parents[5] / 'py'))

from bumbled_device import BumbledDevice
from bumbled_zephyr import create_bumbled_device_for_zephyr
from central_device import SmpCentralDevice


_BUILD_DIR_ARG_PREFIX = '--build-dir'
_PORT = 23456
# TODO: dedup constants.
_UUID_DOORBELL_SERVICE = '7E9648B5-EE32-4B37-9B96-1C5904381BE2'
_UUID_DOORBELL_CHARACTERISTIC = '8AE241C9-8029-4051-890D-071F62C36FE3'


def _find_build_dir() -> str:
    for i, arg in enumerate(sys.argv):
        if arg.startswith(_BUILD_DIR_ARG_PREFIX):
            arg = arg[len(_BUILD_DIR_ARG_PREFIX):]
            if not arg:
                return sys.argv[i + 1]
            if arg[0] == '=':
                return arg[1:]
    raise RuntimeError(f'Cannot find flag: {_BUILD_DIR_ARG_PREFIX}')


@pytest.fixture(name='bumbler')
def fixture_bumbler() -> Callable[LocalLink, BumbledDevice]:
    bin_path = Path(_find_build_dir()) / 'zephyr/zephyr.exe'
    assert bin_path.exists()
    def create(link: LocalLink) -> BumbledDevice:
        return create_bumbled_device_for_zephyr(
            'DUT', _PORT, link, str(bin_path), extra_program_args=[])
    return create


def test_discoverd_and_subscribed(bumbler):
    async def run():
        link = LocalLink()
        async with bumbler(link) as bumbled_device:
            bumbled_device.controller.random_address = ':'.join(['A0'] * 6)
            proc = bumbled_device.process
            try:
                tester_device = SmpCentralDevice('Peer', link)
                tester_device.put_passkey(321098)  # Fixed on DUT.
                await tester_device.power_on()

                async def read():
                    while True:
                        line = await proc.stdout.readline()
                        if not line: break
                        line = line.decode('utf-8')
                        logging.debug('-----STDOUT----- %s', line)
                read_task = asyncio.create_task(read())
                logging.debug('Created read task.')

                conn = await tester_device.connect_with_pairing()
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
            finally:
                logging.debug(f'Final proc exit code: {proc.returncode}')
    asyncio.run(run())
