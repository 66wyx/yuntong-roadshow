# Protocol implementation references

The validation code follows the public wire layouts and field definitions of:

- GB 46750-2025 and the MIT-licensed
  `sd1471123/esp32-ChinaRemoteID_Scan_Sim` receiver implementation.
- ASTM F3411 / OpenDroneID and the Apache-2.0
  `opendroneid/opendroneid-core-c` library.

The Python implementation in this directory is a validation subset. It is not
a certification package and does not establish GB 46750 or ASTM compliance.
