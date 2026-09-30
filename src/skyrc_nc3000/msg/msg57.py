import dataclasses


@dataclasses.dataclass
class Msg57Response:
    unknown: bytes

    @classmethod
    def from_bytes(cls, buf: bytes) -> Msg57Response:
        if buf[0] != 0x57:
            raise ValueError("Not a 0x57 message")

        o = cls.__new__(cls)
        o.unknown = buf[1:]
        return o

    def __str__(self) -> str:
        return "Msg57<" + self.unknown.hex(sep=' ') + ">"
