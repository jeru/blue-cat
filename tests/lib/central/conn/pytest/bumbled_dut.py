# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

import asyncio
from asyncio.subprocess import Process
from pathlib import Path

from bumble.device import Device, DeviceConfiguration
from bumble.host import Host
from bumble.controller import Controller
from bumble.link import LocalLink
from bumble.pairing import PairingConfig, PairingDelegate
from bumble.transport import open_transport, Transport


class BumbledDut:
    build_dir: Path
    port: int
    _transport: Transport | None
    _proc: Process | None

    def __init__(self, build_dir: Path, port: int):
        self.build_dir = build_dir
        self.port = port
        self.bin_path = Path(build_dir, 'zephyr/zephyr.exe')
        if not self.bin_path.exists():
            raise RuntimeError(f'No binary to run: f{self.bin_path}')

    async def __aenter__(self) -> tuple[Process, LocalLink]:
        self._transport = await open_transport(f'tcp-server:_:{self.port}')
        try:
            self._proc, link = await self._setup()
            return (self._proc, link)
        except:
            await self._transport.close()
            self._transport = None
            raise

    async def __aexit__(self, *_args):
        if self._transport:
            await self._transport.close()
            self._transport = None
        if self._proc:
            self._proc.terminate()
            self._proc = None

    async def _setup(self) -> tuple[Process, LocalLink]:
        link = LocalLink()
        controller = Controller(
            'DUT', link=link,
            host_source=self._transport.source,
            host_sink=self._transport.sink)
        controller.random_address = 'A0:A0:A0:A0:A0:A0'
        proc = await asyncio.create_subprocess_exec(
                self.bin_path, f'--bt-dev=127.0.0.1:{self.port}',
                stdout=asyncio.subprocess.PIPE)
        return proc, link


def create_remote_device(link: LocalLink, **extra_config) -> Device:
    delegate = extra_config.get('delegate')
    if delegate: del extra_config['delegate']

    extra_config.setdefault('advertising_interval', 10)  # ms
    extra_config.setdefault('address', 'E0:E0:E0:E0:E0:E0')

    config = DeviceConfiguration()
    config.load_from_dict(extra_config)
    device = Device(config=config)
    device.host = Host()
    device.host.controller = Controller('Remote', link=link)

    if not delegate:
        delegate = PairingDelegate(
            io_capability=PairingDelegate.DISPLAY_OUTPUT_AND_KEYBOARD_INPUT)
    device.pairing_config_factory = lambda conn: PairingConfig(
        delegate=delegate)

    return device
