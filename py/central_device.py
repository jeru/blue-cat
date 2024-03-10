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

from bumble.controller import Controller
from bumble.device import Device
from bumble.host import Connection, Host
from bumble.pairing import PairingConfig, PairingDelegate
from bumble.link import LocalLink


class CentralDevice(Device):
    def __init__(self, name: str, link: LocalLink,
                 delegate: PairingDelegate | None = None,
                 device_listener: Device.Listener | None = None):
        super().__init__()
        self.host = Host()
        self.host.controller = Controller(name, link=link)

        self.delegate = delegate or PairingDelegate(
                io_capability=PairingDelegate.DISPLAY_OUTPUT_AND_KEYBOARD_INPUT)
        self.pairing_config_factory = lambda conn: PairingConfig(
            delegate=self.delegate)

        self.listener = device_listener or Device.Listener()

    async def scan_and_connect(self, wait_for_security_request: bool = False
    ) -> Connection:
        address_queue = asyncio.Queue(1)
        def on_adv(adv):
            assert adv.is_connectable
            address_queue.put_nowait(adv.address)
        self.on('advertisement', on_adv)
        await self.start_scanning()
        address = await address_queue.get()
        await self.stop_scanning()

        connect = await self.connect(address)
        if wait_for_security_request:
            called = asyncio.Event()
            def security_request(_auth_req):
                called.set()
            connect.on('security_request', security_request)
            await called.wait()
        return connect
