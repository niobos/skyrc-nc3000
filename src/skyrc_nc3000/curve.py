import argparse
import asyncio
import json

from skyrc_nc3000 import NC3000


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
