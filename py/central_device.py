import asyncio
import logging

from bumble.controller import Controller
from bumble.device import Device, DeviceConfiguration
from bumble.hci import Address
from bumble.host import Connection, Host
from bumble.pairing import PairingConfig, PairingDelegate
from bumble.link import LocalLink


class SmpCentralDevice(Device):
    _address_queue: asyncio.Queue[Address]
    _auth_req_queue: asyncio.Queue[int]
    _passkey_queue: asyncio.Queue[int]
    _delegate: PairingDelegate

    def __init__(self, name: str, link: LocalLink,
                 delegate: PairingDelegate | None = None,
                 device_listener: Device.Listener | None = None):
        super().__init__(config=_default_config())
        self.host = Host()
        self.host.controller = Controller(name, link=link)

        self._address_queue = asyncio.Queue(1)
        self._auth_req_queue = asyncio.Queue(1)
        self._passkey_queue = asyncio.Queue(1)

        self._delegate = delegate or _DefaultDelegate(self)
        self.pairing_config_factory = lambda conn: PairingConfig(
            delegate=self._delegate)

        self.listener = device_listener or _DefaultDeviceListener(self)

    async def connect_with_pairing(self) -> Connection:
        '''Pairs and connects.

        At some stage during this run (after `self` initiates the pairing
        process), it will wait for `self.put_passkey()`, which should be
        obtained from the other device.
        '''
        await self.start_scanning()
        address = await self._address_queue.get()
        await self.stop_scanning()

        connect = await self.connect(address)
        def security_request(auth_req):
            logging.debug('security_request called. Pairing...')
            self._put_security_request(auth_req)
        # TODO: Use some public interface?
        connect.on('security_request', security_request)

        await self._auth_req_queue.get()
        # `self.put_psaskey()` needed to finish pairing.
        await connect.pair()

        return connect

    def _put_address(self, address: Address):
        self._address_queue.put_nowait(address)

    def _put_security_request(self, auth_req: int):
        self._auth_req_queue.put_nowait(auth_req)

    def put_passkey(self, passkey: int):
        self._passkey_queue.put_nowait(passkey)


def _default_config():
    config = DeviceConfiguration()
    config.load_from_dict(dict(address='E0:E0:E0:E0:E0:E0'))
    return config


class _DefaultDelegate(PairingDelegate):
    device: SmpCentralDevice

    def __init__(self, device: SmpCentralDevice):
        super().__init__(io_capability=
                         PairingDelegate.DISPLAY_OUTPUT_AND_KEYBOARD_INPUT)
        self.device = device

    async def get_number(self):
        logging.debug('Pairing: get number.')
        return await self.device._passkey_queue.get()


class _DefaultDeviceListener(Device.Listener):
    device: SmpCentralDevice

    def __init__(self, device: SmpCentralDevice):
        super().__init__()
        self.device = device

    def on_advertisement(self, advertisement):
        logging.debug('Received advertisement.')
        assert advertisement.is_connectable
        self.device._put_address(advertisement.address)
