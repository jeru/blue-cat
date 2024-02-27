# Connection of the nRF52840 module

Information sources:
* Novelbits.io has quite a nice [brief guide](https://novelbits.io/bluetooth-low-energy-ble-complete-guide/) to BLE.
  Be sure to at least read it through for the basic concepts.
* More details can be found in the [BLE primer](https://www.bluetooth.com/bluetooth-resources/the-bluetooth-low-energy-primer/?utm_source=internal&utm_medium=blog&utm_campaign=technical&utm_content=the-bluetooth-low-energy-primer) from the bluetooth offical site.
* Ultimate ground truth should be the Bluetooth Core Specification ([newest 5.4](https://www.bluetooth.com/specifications/specs/core-specification-5-4/) as of Feb 2024).
* For the security means of BLE, the offical site has a [study guide](https://www.bluetooth.com/bluetooth-resources/le-security-study-guide/) with moderate detail level (enough to find out relevant components in zephyr to enable).

Role assignments:
* The nRF52840 (i.e., blue-cat) module: peripheral.
  - It advertises itself when unconnected.
  - Once connected, asks for Security mode 1 level 4: pair with bonding, encrypted, authenticated.
* The ESP (i.e., chihuahua) module: central. Not covered in this tutorial.

# Basic connection
[Commit](https://github.com/jeru/blue-cat/commit/95b6dc634e22ac36ba444bc9c1e5954de91ded89) for the basic connection without security features.
Logic:
* Kick off advertising at the beginning.
* Once connected, stop advertising.
* Once disconnected, start advertising again.
* Has one zephyr-implemented GATT service "BAS" (battery level service) integrated.
Don't forget to take a look at `prj.conf` as well.

The device has a name `BlueCat`.
Test with nRF Connect mobile version: Scan, then connect.
Should be able to see BAS there, though no one updates its value.

# Secure connection
[Commit](https://github.com/jeru/blue-cat/commit/fd9beef11c921d49be57a0f07fa85af912b1ab58).
* The config change `prj.conf` is probably more tricky to figure out than the actual source code.
* Note that the connection request `bt_conn_set_security(conn, BT_SECURITY_L4);` is only request after the connection is established.
  This should initiate a negotiation for pairing.
* Variable `m_conn_auth_cb` implements some I/O methods, which zephyr uses to derive the capability of information exchange during the bluetooth pairing.
  Here, only `.passkey_display` is implemented, so zephyr will regard it as a display-only device.
* Now, when using nRF Connect to connect to this module, it will print a passkey via SWO; and nRF Connect will ask for that passkey in order to finish pairing.
