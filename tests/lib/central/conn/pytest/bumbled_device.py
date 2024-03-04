# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0

from asyncio.subprocess import Process
from typing import Awaitable

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
        await self._initializer
        return self

    async def __aexit__(self, *args):
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
