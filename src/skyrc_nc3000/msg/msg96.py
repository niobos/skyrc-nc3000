import dataclasses


@dataclasses.dataclass
class Msg96Response:
    unknown: bytes

    @classmethod
    def from_bytes(cls, buf: bytes) -> Msg96Response:
        if buf[0] != 0x96:
            raise ValueError("Not a 0x96 message")

        o = cls.__new__(cls)
        o.unknown = buf[1:]
        return o

    def __str__(self) -> str:
        return "Msg96<" + self.unknown.hex(sep=' ') + ">"
