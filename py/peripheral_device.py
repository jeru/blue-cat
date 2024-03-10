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

from bumble.device import Connection, Device


async def advertise_until_connected(device: Device) -> Connection:
    '''Advertises until a connection is established by some peer device.

    This device will be peripheral.
    '''
    connect_fut = asyncio.Future()
    def on_connection(connect):
        connect_fut.set_result(connect)
    device.on('connection', on_connection)

    await device.start_advertising()
    connect = await connect_fut
    await device.stop_advertising()
    return connect
