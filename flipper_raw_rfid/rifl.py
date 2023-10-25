"""
Classes to load/save a raw rfid file from flipper (xyz.ask.raw or xyz.psk.raw)

Usage:

rifl = RiflFile.load('path/to/raw.ask.raw')
# get header values
frequency = rifl.header.frequency
duty_cycle = rifl.header.duty_cycle
# get pulse and duration values
pd = rifl.pulse_and_durations

"""
from __future__ import annotations

from io import BytesIO
from typing import BinaryIO, Generator, Any
from struct import unpack, pack, error as struct_error
from pathlib import Path
from dataclasses import dataclass

import numpy
import numpy.typing as npt

from flipper_raw_rfid.utils import batched

LFRFID_RAW_FILE_MAGIC = 0x4C464952  # binary string "RIFL"
LFRFID_RAW_FILE_VERSION = 1


class RiflError(ValueError):
    def __init__(self, message: Any, file: BinaryIO = None):
        super().__init__(message)
        self.file = file


@dataclass
class RiflHeader:
    """
    Rifl Header data structure
    """
    version: int
    """ Version of the rifl file format: 1 supported """
    frequency: float
    """ Frequency of the signal in Hz """
    duty_cycle: float
    """ Duty cycle of the signal"""
    max_buffer_size: int
    """ Maximum buffer size in bytes"""

    @staticmethod
    def from_io(io: BinaryIO) -> RiflHeader:
        try:
            return RiflHeader.from_bytes(io.read(20))
        except RiflError as e:
            e.file = io
            raise e

    @staticmethod
    def from_bytes(f: bytes) -> RiflHeader:
        try:
            magic, version, frequency, duty_cycle, max_buffer_size = unpack('IIffI', f)
        except struct_error:
            raise RiflError('Not a RIFL file')
        if magic != LFRFID_RAW_FILE_MAGIC:
            raise RiflError('Not a RIFL file')
        if version != LFRFID_RAW_FILE_VERSION:
            raise RiflError(f'Unsupported RIFL Version {version}')

        return RiflHeader(version, frequency, duty_cycle, max_buffer_size)

    def to_bytes(self) -> bytes:
        return pack('IIffI', LFRFID_RAW_FILE_MAGIC, self.version, self.frequency, self.duty_cycle, self.max_buffer_size)


@dataclass
class Rifl:
    """
    A raw rfid file from flipper (xyz.ask.raw or xyz.psk.raw)

    """
    header: RiflHeader
    """ The header of the file """

    pulse_and_durations: npt.NDArray[numpy.int64] = None
    """
    a nx2 numpy array with:
    column 0: pulse - (number of µs while output high) and
    column 1: duration - (number of µs till next signal)

    Diagram:

    _____________      _____
                 ______     _______________ .......

    ^ - pulse - ^

    ^ -    duration  -^


    """

    @staticmethod
    def load(path: Path | str) -> Rifl:
        path = Path(path)
        with path.open('rb') as f:
            return Rifl.from_io(f)

    @staticmethod
    def from_io(io: BinaryIO) -> Rifl:
        header = RiflHeader.from_io(io)
        pads = numpy.array(list(Rifl._pulse_and_durations(io, header.max_buffer_size)), dtype=numpy.int64)
        return Rifl(header, pads)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        with path.open('wb') as f:
            self.to_io(f)

    def to_io(self, io: BinaryIO) -> None:

        def write(b: BytesIO) -> None:
            io.write(pack('I', b.getbuffer().nbytes))
            io.write(b.getvalue())

        def write_pair(b: BytesIO, pair: BytesIO) -> BytesIO:
            if b.getbuffer().nbytes + pair.getbuffer().nbytes > self.header.max_buffer_size:
                write(b)
                b = BytesIO()
            b.write(pair.getvalue())
            return b

        io.write(self.header.to_bytes())

        buffer = BytesIO()
        for pulse, duration in self.pulse_and_durations:
            pair_buffer = BytesIO()
            Rifl.write_varint(pair_buffer, pulse)
            Rifl.write_varint(pair_buffer, duration)
            buffer = write_pair(buffer, pair_buffer)

        write(buffer)

    @staticmethod
    def _buffers(io: BinaryIO, max_buffer_size: int) -> Generator[BinaryIO, None, None]:
        """
        Read raw binary buffers  and loop through them

        Each buffer holds varint (https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/toolbox/varint.c#L13) encoded pairs
        """
        while True:
            try:
                buffer_size, = unpack('I', io.read(4))
            except struct_error:
                # No more bytes left, EOF
                break
            if buffer_size > max_buffer_size:
                raise RiflError(f'read pair: buffer size is too big  {buffer_size} > {max_buffer_size}', io)
            buffer = io.read(buffer_size)
            if len(buffer) != buffer_size:
                raise RiflError(f'Tried to read  {buffer_size} bytes got only {len(buffer)}', io)
            yield BytesIO(buffer)

    @staticmethod
    def _pulse_and_durations(io: BinaryIO, max_buffer_size: int) -> Generator[tuple[int, int], None, None]:
        """
        loop through buffers and yield a pulse and duration tuple
        """
        for buffer in Rifl._buffers(io, max_buffer_size):
            for pulse, duration in batched(Rifl.read_varint(buffer), 2):
                yield pulse, duration

    @staticmethod
    def read_varint(buffer: BinaryIO) -> Generator[int, None, None]:
        """
        Read one varint from buffer

        Python implementation of https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/toolbox/varint.c#L13

        """
        res = 0
        i = 1
        while (vs := buffer.read(1)) != b'':
            v = vs[0]
            # the low 7 bits are the value
            res = res | (v & 0x7F) * i
            i = i << 7
            # yield when continue bit (bit 8) is not set
            if v & 0x80 == 0:
                yield res
                res = 0
                i = 1

    @staticmethod
    def write_varint(buffer: BinaryIO, value: int) -> int:
        """
        Write one varint to buffer
        """
        i = 1
        while value > 0x80:
            buffer.write(bytes([value & 0x7F | 0x80]))
            value >>= 7
            i += 1

        buffer.write(bytes([value & 0x7F]))
        return i


__all__ = ['Rifl', 'RiflError']
