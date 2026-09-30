import argparse
import asyncio
import datetime
import re
import logging
import sys
from pydoc import pager

import bleak

from . import NC3000


parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="Increase verbosity")
parser.add_argument("--device-address", type=str,
                    help="Connect to this specific device address (MAC on linux, UUID on macOS)")
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


async def main(args):
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
        return

    async with NC3000(device) as nc3000:
        while True:
            try:
                print(datetime.datetime.now())
                status = await asyncio.wait_for(nc3000.get_status(), timeout=0.5)
                print(status)
                for ch in range(1, 8+1):
                    curve = await asyncio.wait_for(nc3000.get_curve(ch), timeout=0.5)
                    total_samples = sum([
                        len(page.voltages_mV)
                        for page in curve
                    ])
                    if total_samples > 0:
                        int = status.channel[ch-1].time_s / total_samples
                        print(f"channel {ch}: {status.channel[ch-1].time_s}s, {total_samples} samples at {curve[0].unknown4}; "
                              f"{int:.1f} s/sample")
                await asyncio.sleep(10)
            except asyncio.TimeoutError:
                print("timeout")


asyncio.run(main(args))
