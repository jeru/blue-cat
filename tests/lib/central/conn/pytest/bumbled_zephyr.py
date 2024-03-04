import asyncio.subprocess
from bumble.link import LocalLink
from bumble.transport.tcp_server import open_tcp_server_transport

from bumbled_device import BumbledDevice


def create_bumbled_device_for_zephyr(
        controller_name: str, port: int, link: LocalLink,
        zephyr_program: str, extra_program_args: list[str]):
    t = open_tcp_server_transport(f'_:{port}')
    p = asyncio.create_subprocess_exec(
        zephyr_program, f'--bt-dev=127.0.0.1:{port}', *extra_program_args,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    return BumbledDevice(controller_name, link, t, p)
