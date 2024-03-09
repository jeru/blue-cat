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

from bumble.controller import Controller
from bumble.device import Device, DeviceConfiguration
from bumble.host import Host
from bumble.pairing import PairingConfig, PairingDelegate
from bumble.link import LocalLink


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
