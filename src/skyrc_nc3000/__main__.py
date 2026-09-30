import argparse
import asyncio
import dataclasses
import json
import re
import logging
import sys

import bleak

from . import NC3000


async def status(con: NC3000, args: argparse.Namespace) -> int:
    out = {}
    status = await asyncio.wait_for(con.get_status(), timeout=0.5)
    for i, ch in enumerate(status.channel):
        out[i+1] = {
            "mode": str(ch.mode),
            "current_mA": ch.current_mA,
            "voltage_mV": ch.voltage_mV,
            "delta_V_mV": ch.delta_V_mV,
            "charge_mAh": ch.charge_mAh,
            "time_s": ch.time_s,
            "internal_resistance_mOhm": ch.internal_resistance_mOhm,
            "unknown4": ch.unknown4,
            "unknown8": ch.unknown8.hex(sep=' '),
            "unknown12": ch.unknown12.hex(sep=' '),
            "unknown15": ch.unknown15.hex(sep=' '),
        }
    print(json.dumps(out, indent=2))
    return 0

async def curve(con: NC3000, args: argparse.Namespace) -> int:
    out = {}
    for ch in args.channel:
        curve = await asyncio.wait_for(con.get_curve(ch), timeout=0.5)
        voltages_mV = []
        for page in curve:
            voltages_mV.extend(page.voltages_mV)
        out[ch] = voltages_mV
    print(json.dumps(out, indent=2))
    return 0


parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="Increase verbosity")
parser.add_argument("--device-address", type=str,
                    help="Connect to this specific device address (MAC on linux, UUID on macOS) "
                         "instead of scanning")
action_parser = parser.add_subparsers()

status_subparser = action_parser.add_parser('status')
status_subparser.set_defaults(action=status)

curve_subparser = action_parser.add_parser('curve')
curve_subparser.set_defaults(action=curve)
curve_subparser.add_argument("--channel", type=int, action='append',
                             help="Output the voltage curve of the given channel(s). "
                                  "Can be specified multiple times")

args = parser.parse_args()

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.WARNING - 10 * args.verbose)
logger.addHandler(handler)


def bluetooth_filter_func(device: bleak.BLEDevice, adv: bleak.AdvertisementData) -> bool:
    if device.name is None:
        return False
    if re.match('#Charger', device.name):
        return True
    return False


async def main(args) -> int:
    if args.device_address is None:
        logger.info("Scanning for devices...")
        device = await bleak.BleakScanner.find_device_by_filter(
            bluetooth_filter_func,
        )
        if device is not None:
            logger.info(f"Found {device.name} ({device.address})")
    else:
        device = await bleak.BleakScanner.find_device_by_address(args.device_address)

    if device is None:
        logger.error('No devices found')
        return 1

    async with NC3000(device) as nc3000:
        rv = await args.action(nc3000, args)

    return rv


rv = asyncio.run(main(args))
sys.exit(rv)
