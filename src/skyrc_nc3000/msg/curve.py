import asyncio
import dataclasses
import logging

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class CurveMsg:
    channel: int
    pages: int
    page: int
    unknown4: int  # sample interval?
    voltages_mV: list[int]  # up to 100 measurements per page

    @classmethod
    def from_bytes(cls, buf: bytes) -> CurveMsg:
        if buf[0] != 0x98:
            raise ValueError("Not a 0x98 message")

        o = cls.__new__(cls)
        o.channel = buf[1]
        o.pages = buf[2]
        o.page = buf[3]
        o.unknown4 = buf[4]

        o.voltages_mV = []
        i = 5
        while i < len(buf):
            o.voltages_mV.append(int.from_bytes(buf[i:i+2], byteorder='little', signed=False))
            i += 2

        return o


class CurveResponse:
    def __init__(self) -> None:
        self._pages: dict[int, CurveMsg] = {}
        self.value: asyncio.Future[list[CurveMsg]] = asyncio.Future()

    def add_page(self, msg: CurveMsg) -> None:
        # ASSUMPTION: pages always arrive in order
        if msg.page == len(self._pages) + 1:
            self._pages[msg.page] = msg
        else:
            logger.warning(f"Received page {msg.page}/{msg.pages}, but still missing page {len(self._pages) + 1}")

        if len(self._pages) == msg.pages:
            self.value.set_result(list(self._pages.values()))
