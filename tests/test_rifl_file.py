from io import BytesIO
from pathlib import Path
from unittest import TestCase

import numpy
from numpy.testing import assert_array_equal

from flipper_raw_rfid.rifl import Rifl, RiflHeader

TEST_BASE_PATH = Path(__file__).parent.absolute()


class RiflFileTest(TestCase):

    example_bytes = bytes.fromhex('f101a903ae028506a604fb05bb028706ad04b90404c403')
    example_ints = [241, 425, 302, 773, 550, 763, 315, 775, 557, 569, 4, 452]

    def test_header_to_bytes_and_back(self):
        header = RiflHeader(1, 125_000, 0.5, 2048)
        self.assertEqual(header, RiflHeader.from_bytes(header.to_bytes()))

    def test_header_checks_magic(self):
        RiflHeader.from_bytes(bytes.fromhex('5249464C 01000000 0024F447 0000003F  00080000'))

        with self.assertRaisesRegex(ValueError, 'Not a RIFL file'):
            RiflHeader.from_bytes(bytes.fromhex('C0FFEEAA 01000000 0024F447 0000003F  00080000'))

    def test_header_checks_version(self):
        header = RiflHeader(2, 125_000, 0.5, 2048)
        with self.assertRaisesRegex(ValueError, 'Unsupported RIFL Version 2'):
            RiflHeader.from_bytes(header.to_bytes())

    def test_read_varint(self):
        buffer = BytesIO(self.example_bytes)
        self.assertEqual(self.example_ints, list(Rifl.read_varint(buffer)))

    def test_write_varint(self):
        buffer = BytesIO()
        for v in self.example_ints:
            Rifl.write_varint(buffer, v)
        self.assertEqual(self.example_bytes, buffer.getvalue())

    def test_to_and_from_io(self):
        # Load file
        rifl = Rifl.load(TEST_BASE_PATH / 'assets' / 'Red354.ask.raw')
        buffer = BytesIO()
        rifl.to_io(buffer)

        # Load from buffer, should be the same
        rifl2 = Rifl.from_io(BytesIO(buffer.getvalue()))
        buffer2 = BytesIO()
        rifl2.to_io(buffer2)

        self.assertEqual(rifl.header, rifl2.header)
        assert_array_equal(rifl.pulse_and_durations, rifl2.pulse_and_durations)
        self.assertEqual(buffer.getvalue(), buffer2.getvalue())

    def test_save_and_load(self):
        dummy_file = TEST_BASE_PATH / 'assets' / 'dummy.ask.raw'

        header = RiflHeader(1, 125000.0, 0.5, 2048)
        pads = numpy.reshape(self.example_ints, (-1, 2))
        dummy1 = Rifl(header, pads)
        dummy1.save(dummy_file)

        dummy2 = Rifl.load(dummy_file)
        self.assertEqual(dummy1.header, dummy2.header)
        assert_array_equal(dummy1.pulse_and_durations, dummy2.pulse_and_durations)

        dummy_file.unlink()
