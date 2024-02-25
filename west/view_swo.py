# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0
'''
A (probably over-hardwired) SWO viewer as a `west` command.
'''

import os
from pathlib import Path
import subprocess
from textwrap import dedent
import yaml

from west import log
from west.commands import WestCommand


_RUNNERS_YAML_PATH = 'zephyr/runners.yaml'
_OPENOCD_CFG_PATH = 'support/openocd.cfg'


def guess_build_dir(build_dir):
    def _try(build_dir):
        path = Path(build_dir).resolve()
        if (path / _RUNNERS_YAML_PATH).exists(): return path
        raise ValueError(dedent(
            f'''Cannot find a build dir containing {_RUNNERS_YAML_PATH}.
            Consider giving explicit --build-dir.'''))
    if build_dir is not None: return _try(build_dir)
    try:
        return _try('.')
    except ValueError:
        return _try('build')


class ViewSwo(WestCommand):
    def __init__(self):
        super().__init__(
            'view-swo',
            'Views the SWO output.',
            dedent('''
            No arg needed. Will start a server and a client.

            The server: `openocd`, presetting `$swo_file` to a named pipe, and
            using `-f ${BOARD_DIR}/support/openocd.cfg`. This config should
            consume `$swo_file` when configuring its TPIU.

            The client: `itmdump` from Rust cargo `itm`, reading the same named
            pipe.
            '''))

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help,
                                         description=self.description)
        parser.add_argument('--build-dir', help='The binary build dir.')
        return parser

    def do_run(self, args, unknown_args):
        build_dir = guess_build_dir(args.build_dir)
        log.inf('build-dir:', build_dir)
        with open(build_dir / _RUNNERS_YAML_PATH) as f:
            runner_yaml = yaml.safe_load(f.read())
        runner_config = runner_yaml['config']
        openocd_path = runner_config['openocd']
        board_dir = runner_config['board_dir']
        openocd_cfg_path = Path(board_dir) / _OPENOCD_CFG_PATH
        if not openocd_cfg_path.exists():
            raise ValueError(f'No {_OPENOCD_CFG_PATH} found in the board dir.')

        named_pipe_path = build_dir / 'openocd-swo.pipe'
        try:
            named_pipe = os.mkfifo(named_pipe_path)
        except FileExistsError:
            pass
        server = subprocess.Popen([
            openocd_path,
            '-c', f'set swo_file "{named_pipe_path}"',
            '-f', openocd_cfg_path])
        try:
            self.check_call(['itmdump', '-f', str(named_pipe_path)])
        finally:
            server.terminate()
            server.wait()
