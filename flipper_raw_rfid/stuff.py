"""
Some useful functions not used in the main code yet
"""
import numpy

from flipper_raw_rfid.utils import find_peaks


def correlation_offset(d1,d2):
    middle = len(d1)//2
    cor = numpy.correlate(d1, d2, mode='same')
    return find_peaks(cor)[0].center - middle


def roll(a, shift):
    """
    Like numpy roll but with padding instead of wrapping around
    :param a: array
    :param shift: amount to shift
    :return: shifted array
    """
    if shift>0:
        return numpy.pad(a[:-shift], (shift, 0))
    else:
        return numpy.pad(a[-shift:], (0, -shift))


def rationalizations(x, rtol=1e-05, atol=1e-08):
    assert 0 <= x
    ix = int(x)
    yield ix, 1
    if numpy.isclose(x, ix, rtol, atol):
        return
    for numer, denom in rationalizations(1.0 / (x - ix), rtol, atol):
        yield denom + ix * numer, numer


def find_fundamental(fs, rtol=1e-3):
    f0 = fs[0]
    res = numpy.zeros((len(fs), 2), dtype=numpy.int32)
    for i, f in enumerate(fs):
        res[i] = list(rationalizations(f0 / f, rtol=rtol))[-1]

    lcm = numpy.lcm.reduce(res[:, 0])
    common = (lcm // res[:, 0] * res.T)[1]
    return numpy.mean(fs / common), common