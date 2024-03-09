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
_KCONFIG_PATH = 'zephyr/.config'
_OPENOCD_CFG_PATH = 'support/openocd.cfg'


def _guess_build_dir(build_dir):
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


def _read_runner_config(build_dir):
    with open(build_dir / _RUNNERS_YAML_PATH) as f:
        runner_yaml = yaml.safe_load(f.read())
    return runner_yaml['config']


def _read_kconfig(build_dir):
    with open(build_dir / _KCONFIG_PATH) as f:
        return dict(tuple(line.rstrip().split('=', maxsplit=1))
                    for line in f if line.startswith('CONFIG_'))


class ViewSwo(WestCommand):
    def __init__(self):
        super().__init__(
            'view-swo',
            'Views the SWO output.',
            dedent('''
            Will start a server and a client.

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
        build_dir = _guess_build_dir(args.build_dir)
        log.inf('build-dir:', build_dir)
        runner_config = _read_runner_config(build_dir)
        kconfig = _read_kconfig(build_dir)

        openocd_path = runner_config['openocd']
        openocd_cfg_path = Path(runner_config['board_dir']) / _OPENOCD_CFG_PATH
        if not openocd_cfg_path.exists():
            raise ValueError(f'No {_OPENOCD_CFG_PATH} found in the board dir.')

        # Named pipe to share between the server and client.
        named_pipe_path = build_dir / 'openocd-swo.pipe'
        try:
            named_pipe = os.mkfifo(named_pipe_path)
        except FileExistsError:
            # Simply reuse existing FIFO from previous runs.
            pass
        # Server: openocd.
        openocd_cmd = [openocd_path]
        openocd_cmd.extend(['-c', f'set swo_file "{named_pipe_path}"'])
        pin_freq = kconfig['CONFIG_LOG_BACKEND_SWO_FREQ_HZ']
        openocd_cmd.extend(['-c', f'set swo_pin_freq {pin_freq}'])
        openocd_cmd.extend(['-f', openocd_cfg_path])
        server = subprocess.Popen(openocd_cmd)
        # Client: itmdump.
        try:
            client = subprocess.Popen(
                    ['itmdump', '-f', str(named_pipe_path)])
            client.wait()
        finally:
            server.terminate()
            server.wait()
