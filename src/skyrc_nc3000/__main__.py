import argparse
import asyncio
import re
import logging
import sys

import bleak

from .curve import curve
from .status import status
from . import NC3000

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="Increase verbosity")
parser.add_argument("--device-address", type=str,
                    help="Connect to this specific device address (MAC on linux, UUID on macOS) "
                         "instead of scanning")
action_parser = parser.add_subparsers(required=True)

status_subparser = action_parser.add_parser('status')
status_subparser.set_defaults(action=status)
status_subparser.add_argument("--format", choices=['table', 'csv', 'json'], default='table')
status_subparser.add_argument("--every", type=int,
                              help="Request status in a loop, every N seconds until interrupted")

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
