import dataclasses


@dataclasses.dataclass
class Msg06Response:
    unknown: bytes

    @classmethod
    def from_bytes(cls, buf: bytes) -> Msg06Response:
        if buf[0] != 0x06:
            raise ValueError("Not a 0x06 message")

        o = cls.__new__(cls)
        o.unknown = buf[1:]
        return o

    def __str__(self) -> str:
        return "Msg06<" + self.unknown.hex(sep=' ') + '>'
