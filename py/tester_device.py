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


def create_tester_device(name: str, link: LocalLink,
                         io_capability: PairingDelegate.IoCapability =
                             PairingDelegate.DISPLAY_OUTPUT_AND_KEYBOARD_INPUT,
                         device_config: DeviceConfiguration = None) -> Device:
    '''Device with both host and controller from bumble.'''
    host = Host()
    host.controller = Controller(name, link=link)

    config = device_config or _default_config(name)
    device = Device(config=config, host=host)

    delegate = PairingDelegate(io_capability)
    device.pairing_config_factory = lambda _: PairingConfig(delegate=delegate)

    device.listener = Device.Listener()
    return device


def _default_config(name: str) -> DeviceConfiguration:
    config = DeviceConfiguration()
    config.load_from_dict({'name': name})
    return config
