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

import asyncio.subprocess
import os.path
import sys

from bumble.link import LocalLink
from bumble.transport.tcp_server import open_tcp_server_transport
from bumbled_device import BumbledDevice


_BUILD_DIR_ARG_PREFIX = '--build-dir'


def create_bumbled_device_for_zephyr(
        controller_name: str, port: int, link: LocalLink,
        zephyr_program: str, extra_program_args: list[str] | None = None
) -> BumbledDevice:
    transport = open_tcp_server_transport(f'_:{port}')
    process = asyncio.create_subprocess_exec(
        zephyr_program, f'--bt-dev=127.0.0.1:{port}',
        *(extra_program_args or []),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    return BumbledDevice(controller_name, link, transport, process)


def find_zephyr_binary_from_env() -> str:
    def find_build_dir() -> str:
        for i, arg in enumerate(sys.argv):
            if arg.startswith(_BUILD_DIR_ARG_PREFIX):
                arg = arg[len(_BUILD_DIR_ARG_PREFIX):]
                if not arg:
                    return sys.argv[i + 1]
                if arg[0] == '=':
                    return arg[1:]
        raise RuntimeError(f'Cannot find flag: {_BUILD_DIR_ARG_PREFIX}')
    bin_path = os.path.join(find_build_dir(), 'zephyr', 'zephyr.exe')
    assert os.path.exists(bin_path), f"Doesn't exist: f{bin_path}"
    return bin_path
