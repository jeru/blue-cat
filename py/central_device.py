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
from typing import Awaitable

from bumble.device import Connection, Device


async def scan_and_connect(device: Device) -> (Connection, Awaitable[int]):
    '''Scans and connects to the device from the first advertisement.

    This device will be central.

    Returns:
    * The established connection.
    * An object to receive a potential security request if the peer device
      requires so. The int is the auth request, a bit map. Note that if the
      peer doesn't request a security request, awaiting for it will be blocking
      forever.
    '''
    address_fut = asyncio.Future()
    def on_advertisement(adv):
        assert adv.is_connectable
        address_fut.set_result(adv.address)
    device.on('advertisement', on_advertisement)
    await device.start_scanning()
    address = await address_fut
    await device.stop_scanning()

    connect = await device.connect(address)
    # Registering of the security request must be close to the connection
    # creation, best not broken up. Otherwise, if the peer device requires
    # it before it is registered, the message will be lost.
    called = asyncio.Event()
    def security_request(_auth_req):
        called.set()
    connect.on('security_request', security_request)

    return (connect, called.wait())
