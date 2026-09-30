import asyncio
import logging
import time
import typing

import bleak
import bleak_retry_connector

from . import msg

NC3000_CHARACTERISTIC_UUID: typing.Final = "0000ffe1-0000-1000-8000-00805f9b34fb"

WAIT_BETWEEN_TX = 0.01

CMD_GET_CURVE: typing.Final = 0x98
CMD_GET_STATUS: typing.Final = 0x9a

logger = logging.getLogger(__name__)


class NC3000:
    def __init__(self, device: bleak.BLEDevice):
        self._device = device

        self._client: bleak.BleakClient | None = None
        self._pending_requests: dict[int, asyncio.Future] = {}

        self._tx_throttle = time.time()
        self._tx_lock = asyncio.Lock()

        self._curve: dict[int, msg.curve.CurveResponse] = {}

    def disconnected(self, client: bleak.BleakClient) -> None:
        if self._client is not None:
            logger.warning(f"Disconnected from {client.address}")

    async def __aenter__(self):
        logging.debug(f"Connecting to {self._device.address}...")
        self._client = await bleak_retry_connector.establish_connection(
            bleak_retry_connector.BleakClientWithServiceCache,
            self._device,
            name=self._device.name or "Unknown Device",
            max_attempts=3,
            disconnected_callback=self.disconnected,
            )

        await self._client.start_notify(
            NC3000_CHARACTERISTIC_UUID,
            callback=self.notification,
        )
        await asyncio.sleep(0.5)  # packets sent immediately after start_notify() seems to be silently dropped
        logging.debug(f"Connected to {self._device.address}")

        # First message seems to be used to respond with a 0x06 response, but is otherwise ignored
        await self._send_packet(self._build_packet(bytes([0x57, 1] + [0] * 16)))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Disconnecting from {self._device.address}")
        client = self._client
        self._client = None  # mark client as None to suppress disconnected warning
        await client.disconnect()

    def assert_connected(self) -> None:
        if self._client is None:
            raise RuntimeError("Not connected to device")

    def notification(self, char: bleak.BleakGATTCharacteristic, data: bytearray) -> None:
        logger.debug(f"Rx from {char}: {data.hex(sep=' ')}")

        if data[0] != 0x0f:
            logger.warning(f"Received data without 0x0f header: {data.hex()}")
            return

        length = data[1]
        if len(data) != 2 + length:
            logger.warning(f"Received {len(data)-2} bytes of data with length {length}: {data.hex()}")
            if len(data) < 2+length:
                return
            # else: truncate to length and try
            data = data[0:(2+length)]

        calculated_checksum = sum(data[2:-1]) & 255
        received_checksum = data[-1]
        if calculated_checksum != received_checksum:
            logger.warning(f"Checksum mismatch: calculated {calculated_checksum} != received {received_checksum}")
            return

        data = data[2:-1]
        self.parse_msg(data)

    def parse_msg(self, data: bytearray) -> None:
        cmd = data[0]
        try:
            klass = msg.dispatch[cmd]
            data = klass.from_bytes(data)
            logger.info(f"Rx: {data}")
        except KeyError:
            logger.info(f"Rx: {data.hex(sep=' ')}")

        if isinstance(data, msg.curve.CurveMsg):
            self._curve[data.channel].add_page(data)

        try:
            fut = self._pending_requests[cmd]
            fut.set_result(data)
            del self._pending_requests[cmd]
        except KeyError:
            pass

    async def _query(self, cmd: int, msg: bytes):
        self.assert_connected()

        try:
            fut = self._pending_requests[cmd]
            if fut.cancelled():
                raise KeyError()
        except KeyError:
            fut = asyncio.Future()
            self._pending_requests[cmd] = fut

            await self._send_packet(self._build_packet(msg))

        return await fut

    async def get_status(self) -> msg.status.StatusResponse:
        return await self._query(CMD_GET_STATUS, msg.status.StatusRequest)

    async def get_57(self) -> msg.msg57.Msg57Response:
        return await self._query(0x57, bytes([0x57, 1] + [0] * 16))

    async def get_96(self) -> msg.msg96.Msg96Response:
        return await self._query(0x96, bytes([0x96, 4]),)

    async def get_curve(self, channel: int) -> list[msg.curve.CurveMsg]:
        if not 1 <= channel <= 8:
            raise ValueError(f"Channel {channel} is out of range")

        if channel in self._curve:
            if not self._curve[channel].value.done():
                return await self._curve[channel].value
        # else:

        self._curve[channel] = msg.curve.CurveResponse()
        await self._send_packet(self._build_packet(bytes([CMD_GET_CURVE, channel])))
        resp = await self._curve[channel].value
        del self._curve[channel]
        return resp

    @staticmethod
    def _build_packet(payload: bytearray | bytes) -> bytes:
        packet = bytes(payload)
        packet += bytes([
            sum(packet) & 255
        ])
        packet = bytes([0x0f, len(packet)]) + packet
        return packet

    async def _send_packet(self, packet: bytes) -> None:
        async with self._tx_lock:
            now = time.time()
            to_wait = self._tx_throttle + WAIT_BETWEEN_TX - now
            if to_wait > 0:
                await asyncio.sleep(to_wait)

            logger.debug(f"Tx: {packet.hex(sep=' ')}")
            await self._client.write_gatt_char(
                NC3000_CHARACTERISTIC_UUID,
                packet,
                response=False,  # Service only advertises "WriteWithoutResponse"
            )

            self._tx_throttle = now
