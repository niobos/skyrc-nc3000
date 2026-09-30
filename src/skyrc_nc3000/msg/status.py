import dataclasses
import enum
import typing

StatusRequest = bytes([0x9a, 0])

@dataclasses.dataclass
class StatusResponse:
    unknown1: bytes  # always 0000 ?
    channel: list[ChannelStatus]

    @classmethod
    def from_bytes(cls, buf: bytes) -> StatusResponse:
        if buf[0] != 0x9a:
            raise ValueError("Not a 0x9a message")

        o = cls.__new__(cls)
        o.unknown1 = buf[1:3]

        o.channel = []
        for i in range(8):
            o.channel.append(ChannelStatus.from_bytes(
                buf[3+i*17:3+(i+1)*17]
            ))
        return o

    def __str__(self) -> str:
        return f"Status<{self.unknown1.hex(sep=' ')} \n    " + \
            "\n    ".join(str(_) for _ in self.channel) + \
            ">"

@dataclasses.dataclass
class ChannelStatus:
    current_mA: int
    voltage_mV: int
    unknown4: int
    delta_V_mV: int
    charge_mAh: int
    unknown8: bytes
    time_s: int
    unknown12: bytes
    internal_resistance_mOhm: int
    mode: Mode | int
    unknown15: bytes  # seen: 0000, 0100

    @classmethod
    def from_bytes(cls, buf: bytes) -> ChannelStatus:
        if len(buf) != 17:
            raise ValueError(f"Invalid length {len(buf)} for {cls.__name__}")

        o = cls.__new__(cls)
        o.current_mA = int.from_bytes(buf[0:2], byteorder="big", signed=False)
        o.voltage_mV = int.from_bytes(buf[2:4], byteorder="big", signed=True)
        o.unknown4 = buf[4]
        o.delta_V_mV = buf[5]
        o.charge_mAh = int.from_bytes(buf[6:8], byteorder="big", signed=False)
        o.unknown8 = buf[8:10]
        o.time_s = int.from_bytes(buf[10:12], byteorder="big", signed=False)
        o.unknown12 = buf[12:13]
        o.internal_resistance_mOhm = int.from_bytes(buf[13:14], byteorder="big", signed=False)
        o.mode = try_enum(Mode, buf[14])
        o.unknown15 = buf[15:17]
        return o

    def __str__(self) -> str:
        return (f"["
                f"I={self.current_mA}mA "
                f"U={self.voltage_mV}mV "
                f"{self.unknown4} "
                f"∆V={self.delta_V_mV}mV "
                f"C={self.charge_mAh}mAh "
                f"{self.unknown8.hex(sep=' ')} "
                f"t={self.time_s}s "
                f"{self.unknown12.hex(sep=' ')} "
                f"IR={self.internal_resistance_mOhm}mOhm "
                f"{self.mode} "
                f"{self.unknown15.hex(sep=' ')}"
                f"]")

class Mode(enum.Enum):
    Idle = 0
    Charging = 2
    Discharging = 3
    Charged = 5
    Discharged = 6


T = typing.TypeVar("T", bound=enum.Enum)
def try_enum(enum_class: type[T], value: int) -> T | int:
    try:
        return enum_class(value)
    except ValueError:
        return value
