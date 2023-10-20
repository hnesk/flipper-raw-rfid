from itertools import islice
from typing import Iterable, Any, Generator, cast

import numpy
import numpy.typing as npt
from scipy import ndimage

try:
    # python 3.12?
    from itertools import batched  # type: ignore[attr-defined]
except ImportError:
    def batched(iterable: Iterable[Any], n: int) -> Iterable[tuple[Any, ...]]:
        # batched('ABCDEFG', 3) --> ABC DEF G
        if n < 1:
            raise ValueError('n must be at least one')
        it = iter(iterable)
        while batch := tuple(islice(it, n)):
            yield batch

Signal = npt.NDArray[numpy.int8]
PulseAndDurations = npt.NDArray[numpy.int64]


def pad_to_signal(pulse_and_durations: PulseAndDurations) -> Signal:
    length = pulse_and_durations[:, 1].sum()
    signal = numpy.zeros(length, dtype=numpy.int8)

    position = 0
    for pulse, duration in pulse_and_durations:
        # Fill signal with ones for pulse
        signal[position:position + pulse] = 1
        # Fill signal with zeros for the rest of the duration (not needed, because signal default to zero, just for clarity)
        # signal[position+pulse:position+duration] = 0
        position += duration

    return signal


def signal_to_pad(signal: Signal) -> PulseAndDurations:
    def it(s: Signal) -> Generator[tuple[int, int], None, None]:
        position = -1
        changes = numpy.where(s[:-1] != s[1:])[0]
        for p in batched(changes, 2):
            if len(p) == 2:
                yield p[0] - position, p[1] - position
                position = p[1]

        if len(p) == 1:
            yield p[0] - position, len(s) - position - 1

    return numpy.array(list(it(signal)))


def autocorrelate(x: npt.NDArray[Any]) -> npt.NDArray[numpy.float64]:
    """
    Fast statistical autocorrelation from:
    https://stackoverflow.com/a/51168178
    autocorr3 / fft, pad 0s, non partial
    """

    n = len(x)
    # pad 0s to 2n-1
    ext_size = 2 * n - 1
    # nearest power of 2
    fsize = 2 ** numpy.ceil(numpy.log2(ext_size)).astype('int')

    xp = x - numpy.mean(x)
    var = numpy.var(x)

    # do fft and ifft
    cf = numpy.fft.fft(xp, fsize)
    sf = cf.conjugate() * cf
    corr = numpy.fft.ifft(sf).real
    corr = corr / var / n

    return corr[:len(corr) // 2]


def smooth(signal: Signal, sigma: float = 10) -> npt.NDArray[numpy.float64]:
    return cast(npt.NDArray[numpy.float64], ndimage.gaussian_filter1d(numpy.float32(signal), sigma=sigma, mode='nearest'))


def binarize(signal: npt.NDArray[numpy.float32], threshold: float = 0.5) -> Signal:
    return cast(Signal, numpy.int8(signal > threshold))


__all__ = ['PulseAndDurations', 'Signal', 'signal_to_pad', 'pad_to_signal', 'smooth', 'binarize', 'autocorrelate', 'batched']
