import argparse
import asyncio
import json
import csv
import sys
import time

import tabulate
from ansi_escapes import ansi_escapes

from . import NC3000
from . import msg


CSV_COLS = [
    "time",
    "channel",
    "mode",
    "status",
    "current_mA",
    "voltage_mV",
    "delta_V_mV",
    "charge_mAh",
    "time_s",
    "internal_resistance_mOhm",
    "unknown4",
    "unknown8",
    "unknown12",
    "unknown15",
]

def channel_to_dict(ch: msg.status.ChannelStatus) -> dict:
    return {
        "status": str(ch.status).lstrip("Status."),
        "mode": str(ch.mode).lstrip("Mode."),
        "current_mA": ch.current_mA,
        "voltage_mV": ch.voltage_mV,
        "delta_V_mV": ch.delta_V_mV,
        "charge_mAh": ch.charge_mAh,
        "time_s": ch.time_s,
        "internal_resistance_mOhm": ch.internal_resistance_mOhm,
        "unknown4": ch.unknown4,
        "unknown8": ch.unknown8.hex(sep=' '),
        "unknown12": ch.unknown12.hex(sep=' '),
        "unknown16": ch.unknown16,
    }

async def status_once(con: NC3000, args: argparse.Namespace, csv_writer: csv.DictWriter = None) -> int:
    now = time.time()
    status = await asyncio.wait_for(con.get_status(), timeout=0.5)

    if args.format == 'json':
        out = {
            i+1: channel_to_dict(ch)
            for i, ch in enumerate(status.channel)
        }
        out["time"] = now
        print(json.dumps(out, indent=2))

    elif args.format == 'csv':
        for i, channel in enumerate(status.channel):
            csv_writer.writerow({
                "time": now,
                "channel": i+1,
                **channel_to_dict(channel),
            })

    elif args.format == 'table':
        cols = ["channel",
                "mode",
                "status",
                "current_mA",
                "voltage_mV",
                "delta_V_mV",
                "charge_mAh",
                "time_s",
                "internal_resistance_mOhm",
                "unknown4",
                "unknown8",
                "unknown12",
                "unknown16"]
        rows = []
        for i, channel in enumerate(status.channel):
            channel_data_dict = channel_to_dict(channel)
            rows.append([i+1] + [
                channel_data_dict[col_name]
                for col_name in cols[1:]
            ])
        print(tabulate.tabulate(
            rows,
            headers=cols,
        ))

    else:
        raise NotImplementedError()

    return 0


async def status(con: NC3000, args: argparse.Namespace) -> int:
    if args.format is None:
        args.format = 'table'

    if args.format == 'csv':
        csv_writer = csv.DictWriter(
            sys.stdout, fieldnames=CSV_COLS,
            quoting=csv.QUOTE_NONNUMERIC,
        )
        csv_writer.writeheader()
    else:
        csv_writer = None

    while True:
        rv = await status_once(con, args, csv_writer)
        if args.every is None:
            return rv
        # else:
        await asyncio.sleep(args.every)

        if args.format == 'table':
            print(ansi_escapes.eraseLines(2+8+1), end='')

    # unreachable
