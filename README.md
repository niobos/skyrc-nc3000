SkyRC NC3000 Octa reader
========================

Absolute minimal project to read out the status data for the SkyRC NC3000 Octa charger.

Heavily inspired by [skyrc-ble], [ha-skyrc] and [SkyCharger].

[skyrc-ble]: https://github.com/kroimon/skyrc-ble
[ha-skyrc]: https://github.com/lightheaded/ha-skyrc/
[SkyCharger]: https://github.com/sidhantgoel/SkyCharger

Usage
=====

```
$ .venv/bin/python -m skyrc_nc3000 --help
usage: python -m skyrc_nc3000 [-h] [-v] [--device-address DEVICE_ADDRESS] {status,curve} ...

positional arguments:
  {status,curve}

options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity (default: 0)
  --device-address DEVICE_ADDRESS
                        Connect to this specific device address (MAC on linux, UUID on macOS) instead of scanning (default: None)

$ .venv/bin/python -m skyrc_nc3000 status --help
usage: python -m skyrc_nc3000 status [-h] [--format {table,csv,json}] [--every EVERY]

options:
  -h, --help            show this help message and exit
  --format {table,csv,json}
  --every EVERY         Request status in a loop, every N seconds until interrupted

$ .venv/bin/python -m skyrc_nc3000 curve --help
usage: python -m skyrc_nc3000 curve [-h] [--channel CHANNEL]

options:
  -h, --help         show this help message and exit
  --channel CHANNEL  Output the voltage curve of the given channel(s). Can be specified multiple times
```

```
$ .venv/bin/python -m skyrc_nc3000 status
  channel  mode       status         current_mA    voltage_mV    delta_V_mV    charge_mAh    time_s    internal_resistance_mOhm    unknown4  unknown8      unknown12    unknown16
---------  ---------  -----------  ------------  ------------  ------------  ------------  --------  --------------------------  ----------  ----------  -----------  -----------
        1  Charge     Charging             1022          1472             0            16        78                          14           0  00 00                00            0
        2  Discharge  Discharging           799          1325             0            13        67                          15           0  00 00                00            0
        3  Discharge  Idle                    0             0             0             0         0                           0           0  00 00                00            0
        4  Discharge  Idle                    0             0             0             0         0                           0           0  00 00                00            0
        5  Cycle      Charging             1000          1437             0             6        37                          39           0  00 00                00            0
        6  Charge     Idle                    0          1440             0             0         0                           0           0  00 00                00            0
        7  Discharge  Idle                    0             0             0             0         0                           0           0  00 00                00            0
        8  Discharge  Idle                    0             0             0             0         0                           0           0  00 00                00            0
```
