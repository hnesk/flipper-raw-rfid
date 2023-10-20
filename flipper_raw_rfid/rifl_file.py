"""
Classes to load a raw rfid file from flipper (xyz.ask.raw or xyz.psk.raw)

Usage:

rifl = RiflFile.load('path/to/raw.ask.raw')
# for the binary signal
signal = rifl.signal()
# or for pulse and duration values
pd = rifl.pulse_and_durations()

frequency = rifl.header.frequency
duty_cycle = rifl.header.duty_cycle


"""
from __future__ import annotations

from typing import BinaryIO, Generator, Any
from struct import unpack, error as struct_error
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager

import numpy

from flipper_raw_rfid.utils import batched, pad_to_signal, Signal, PulseAndDurations

LFRFID_RAW_FILE_MAGIC = 0x4C464952  # binary string "RIFL"
LFRFID_RAW_FILE_VERSION = 1


class RiflError(ValueError):
    def __init__(self, message: Any, file: BinaryIO):
        super().__init__(message)
        # Now for your custom code...
        self.file = file


@dataclass
class RiflHeader:
    """
    Rifl Header data structure
    """

    magic: int
    version: int
    frequency: float
    duty_cycle: float
    max_buffer_size: int

    @staticmethod
    def from_bytes(f: BinaryIO) -> RiflHeader:
        try:
            magic, version, frequency, duty_cycle, max_buffer_size = unpack('IIffI', f.read(20))
        except struct_error:
            raise RiflError('Not a RIFL file', f)
        if magic != LFRFID_RAW_FILE_MAGIC:
            raise RiflError('Not a RIFL file', f)
        if version != LFRFID_RAW_FILE_VERSION:
            raise RiflError(f'Unsupported RIFL Version {version}', f)

        return RiflHeader(magic, version, frequency, duty_cycle, max_buffer_size)


@dataclass
class RiflFile:
    """
    A raw rfid file from flipper (xyz.ask.raw or xyz.psk.raw)

    """
    header: RiflHeader
    f: BinaryIO
    _pulse_and_durations = None

    @staticmethod
    def load(path: Path | str) -> RiflFile:
        with RiflFile.open(path) as rifl:
            # Read the file completely
            rifl.pulse_and_durations()
            return rifl

    @staticmethod
    @contextmanager
    def open(path: Path | str) -> Generator[RiflFile, None, None]:
        path = Path(path)
        with path.open('rb') as f:
            yield RiflFile.from_bytes(f)

    @staticmethod
    def from_bytes(f: BinaryIO) -> RiflFile:
        header = RiflHeader.from_bytes(f)
        return RiflFile(header, f)

    @property
    def buffers(self) -> Generator[bytes, None, None]:
        """
        Read raw binary buffers  and loop through them

        Each buffer holds varint (https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/toolbox/varint.c#L13) encoded pairs
        """
        while True:
            try:
                buffer_size, = unpack('I', self.f.read(4))
            except struct_error:
                # No more bytes left, EOF
                break
            if buffer_size > self.header.max_buffer_size:
                raise RiflError(f'read pair: buffer size is too big  {buffer_size} > {self.header.max_buffer_size}', self.f)
            buffer = self.f.read(buffer_size)
            if len(buffer) != buffer_size:
                raise RiflError(f'Tried to read  {buffer_size} bytes got only {len(buffer)}', self.f)
            yield buffer

    def pulse_and_durations_generator(self) -> Generator[tuple[int, int], None, None]:
        """
        loop through buffers and yield a pulse and duration tuple
        """
        for buffer in self.buffers:
            for pulse, duration in batched(RiflFile.read_varint(buffer), 2):
                yield pulse, duration

    def pulse_and_durations(self) -> PulseAndDurations:
        """
        a nx2 numpy array with:
        column 0: pulse - (number of samples while output high) and
        column 1: duration - (number of samples till next signal)

        Diagram:

        _____________      _____
                     ______     _______________ .......

        ^ - pulse - ^

        ^ -    duration  -^


        """

        if self._pulse_and_durations is None:
            self._pulse_and_durations = numpy.array(list(self.pulse_and_durations_generator()))
        return self._pulse_and_durations

    def signal(self) -> Signal:
        """
        Reconstruct a binary signal from pulse and duration
        """
        return pad_to_signal(self.pulse_and_durations())

    @staticmethod
    def read_varint(buffer: bytes) -> Generator[int, None, None]:
        """
        Read one varint from buffer
        """
        pos = 0
        buffer_size = len(buffer)
        while pos < buffer_size:
            value, bytes_read = RiflFile._varint_unpack(buffer, pos, buffer_size)
            pos += bytes_read
            yield value

    @staticmethod
    def _varint_unpack(buffer: bytes, pos: int, size: int) -> tuple[int, int]:
        """
        Python implementation of https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/toolbox/varint.c#L13
        """

        res = 0
        i = 0
        for i in range(0, size - pos):
            v = buffer[i + pos]
            res = res | (v & 0x7F) << (7 * i)
            # Read as long high bit set
            if v & 0x80 == 0:
                break

        return res, i + 1


__all__ = ['RiflFile', 'RiflError']
