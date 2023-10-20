from itertools import zip_longest
from pathlib import Path
from unittest import TestCase

import numpy
from numpy.testing import assert_array_equal

from flipper_raw_rfid import RiflFile
from flipper_raw_rfid.utils import pad_to_signal, signal_to_pad

TEST_BASE_PATH = (Path(__file__).parent).absolute()


class UtilsTest(TestCase):

    @property
    def a_signal(self):
        signal = numpy.zeros(10000, dtype=numpy.int8)
        start = 0
        signal[start:start + 310] = 1
        start += 515
        signal[start:start + 274] = 1
        start += 527
        signal[start:start + 252] = 1
        start += 743
        signal[start:start + 291] = 1
        start += 534
        signal[start:start + 515] = 1
        start += 1016
        signal[start:start + 266] = 1
        start += 515

        return signal[:start]

    @property
    def a_pad(self):
        return numpy.array([
            [310, 515],
            [274, 527],
            [252, 743],
            [291, 534],
            [515, 1016],
            [266, 515]
        ])

    def load(self, file: str | Path) -> RiflFile:
        return RiflFile.load(TEST_BASE_PATH / 'assets' / file)

    def test_pad_to_signal(self):

        signal = pad_to_signal(self.a_pad)

        # First row, a pulse from 0-309 then a zero from 310 - 514
        self.assertEqual(signal[0], 1)
        self.assertEqual(signal[309], 1)
        self.assertEqual(signal[310], 0)
        self.assertEqual(signal[514], 0)

        # Second row, a pulse for 274 samples starting at 515
        self.assertEqual(signal[515], 1)
        self.assertEqual(signal[515 + 273], 1)
        self.assertEqual(signal[515 + 274], 0)
        self.assertEqual(signal[515 + 527 - 1], 0)

        self.assertEqual(signal[515 + 527], 1)
        # and so on

        assert_array_equal(signal, self.a_signal)

    def test_signal_to_pad(self):
        pad = signal_to_pad(self.a_signal)
        assert_array_equal(pad, self.a_pad)

    def test_signal_to_pad_and_back(self):

        def test(signal):
            rec_signal = pad_to_signal(signal_to_pad(signal))
            assert_array_equal(signal, rec_signal)

        test(self.a_signal)
        test(self.load('Red354b.ask.raw').signal())

    def test_pad_to_signal_and_back(self):

        def test(pad):
            rec_pad = signal_to_pad(pad_to_signal(pad))

            pos = 0
            for i, (pd, rpd) in enumerate(zip_longest(pad, rec_pad)):
                if not numpy.array_equal(pd, rpd):
                    assert_array_equal(pd, rpd, err_msg=f'Difference in reconstructed pad in row {i}, sample {pos}')
                pos += pd[1]

        test(self.a_pad)
        test(self.load('Red354b.ask.raw').pulse_and_durations())
        # This fails because of 0 pulse width
        # test(self.load_pad('Red354.ask.raw'))
