# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

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
from bumbled_zephyr import create_bumbled_device_for_zephyr
from central_device import SmpCentralDevice


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
