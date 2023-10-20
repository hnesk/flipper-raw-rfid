#! /usr/bin/python3
"""flipper-raw-rfid

Description:
    Reads a raw rfid file from flipper zero and plots or converts the signal

Usage:
    flipper-raw-rfid convert [-f <format>] RAW_FILE [OUTPUT_FILE]
    flipper-raw-rfid plot RAW_FILE
    flipper-raw-rfid (-h | --help)
    flipper-raw-rfid --version

Arguments:
    RAW_FILE        The raw rfid file from flipper (xyz.ask.raw or xyz.psk.raw)
    OUTPUT_FILE     The converted file as csv (default: stdout)

Options:
    -h --help                 Show this screen.
    --version                 Show version.
    -f --format=(pad|signal)  Output format: "pad" (=Pulse And Duration) is the internal format of the Flipper Zero,
                              each line represents a pulse and a duration value measured in samples, see
                              "Pulse and duration format" below.
                              In "signal" format the pulses are written out as a reconstructed signal with a "1" marking a
                              sample with high value and "0" marking a sample with low value [default: pad]

Pulse and duration format:

    column 0: pulse - (number of samples while output high) and
    column 1: duration - (number of samples till next signal)

    Diagram:

    ______________      __________
                  ______          __________ .......

    ^ - pulse0 - ^      ^-pulse1-^           .......
    ^ -    duration0  -^^ -    duration1  -^ .......

    The csv file has the following format:

    pulse0, duration0
    pulse1, duration1
    ....

"""
import contextlib
import csv
import os
import sys
from typing import Any, Generator, Iterable, IO

from docopt import docopt, printable_usage
from flipper_raw_rfid import RiflFile, RiflError, __version__, pad_to_signal


@contextlib.contextmanager
def smart_open(filename: str, mode: str = 'r', *args: Any, **kwargs: Any) -> Generator[IO[Any], None, None]:
    '''Open files and i/o streams transparently.'''
    fh: IO[Any]
    if filename == '-' or filename is None:
        if 'r' in mode:
            stream = sys.stdin
        else:
            stream = sys.stdout
        if 'b' in mode:
            fh = stream.buffer
        else:
            fh = stream
        close = False
    else:
        fh = open(filename, mode, *args, **kwargs)
        close = True

    try:
        yield fh
        fh.flush()
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, fh.fileno())
    finally:
        if close:
            try:
                fh.close()
            except AttributeError:
                pass


def assert_in(value: Any, vset: Iterable[Any], name: str = 'Value') -> None:
    if value not in vset:
        raise ValueError(f'{name} must be one of: {"/".join(vset)} but was "{value}"')


def convert(raw: str, output: str, format: str = 'pad') -> int:
    assert_in(format, {'signal', 'pad'}, 'Format')
    with smart_open(output, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        rifl = RiflFile.load(raw)
        pads = rifl.pulse_and_durations()
        if format == 'pad':
            for pulse_and_duration in pads:
                csvwriter.writerow(pulse_and_duration)
        elif format == 'signal':
            signal = pad_to_signal(pads)
            csvwriter.writerows(signal.reshape((-1, 1)))

    return 0


def plot(raw: str) -> int:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        raise RuntimeError('For the plot command you need matplotlib, install it with: pip install matplotlib')
    rifl = RiflFile.load(raw)
    pads = rifl.pulse_and_durations()
    signal = pad_to_signal(pads)
    fig, ax = plt.subplots()
    ax.set(xlabel='Samples', ylabel='Signal', title='Reconstructed Signal')
    ax.set_xlim(0, 20000)
    ax.plot(signal)
    plt.show()

    return 0


def process(args: dict[str, Any]) -> int:
    try:
        if args['convert']:
            return convert(args['RAW_FILE'], args['OUTPUT_FILE'], args['--format'])
        elif args['plot']:
            return plot(args['RAW_FILE'])
        else:
            print(printable_usage(__doc__))
            return 1
    except RiflError as e:
        print(printable_usage(__doc__))
        print(f'Error: {e}: {e.file.name if e.file.name else ""}')
        return 1
    except (ValueError, FileNotFoundError, IsADirectoryError, RuntimeError) as e:
        print(printable_usage(__doc__))
        print(f'Error: {e}')
        return 1


def main() -> int:
    args = docopt(__doc__, version=f'flipper-raw-rfid {__version__}')
    return process(args)
