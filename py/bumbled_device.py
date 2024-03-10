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

from asyncio.subprocess import Process
from typing import Awaitable
import logging

from bumble.controller import Controller
from bumble.link import LocalLink
from bumble.transport import Transport


class BumbledDevice:
    _initializer: Awaitable[None]

    transport: Transport | None
    controller: Controller | None
    process: Process | None

    def __init__(self, name: str, link: LocalLink,
                 transport: Awaitable[Transport],
                 process: Awaitable[Process]):
        async def init():
            try:
                self.transport = await transport
                self.controller = Controller(
                    name, link=link, host_source=self.transport.source,
                    host_sink=self.transport.sink)
                self.process = await process
            except:
                await self._close()
                raise
        self._initializer = init()
        self.transport = None
        self.controller = None
        self.process = None

    async def __aenter__(self):
        logging.debug('BumbledDevice.__aenter__')
        await self._initializer
        return self

    async def __aexit__(self, *args):
        logging.debug('BumbledDevice.__aexit__')
        await self._close()

    async def _close(self):
        if self.process:
            self.process.terminate()
            self.process = None
        if self.controller:
            self.controller = None
        if self.transport:
            await self.transport.close()
            self.transport = None
