# Flipper Zero Raw RFID Tools

A python library for reading and analyzing Flipper Zero raw RFID files (`tag.[ap]sk.raw`)
 * [Installation](#installation)
    * [Via pip](#via-pip)
    * [From source](#from-source)
 * [Usage](#usage)
   * [As a library](#as-a-library)
   * [From commandline](#from-commandline)
 * [Tutorial](#tutorial)
 
## Installation

### Via pip

```bash
pip install flipper-raw-rfid
```

### From source
```bash
git clone https://github.com/hnesk/flipper-raw-rfid.git 
cd flipper-raw-rfid
make install
```


## Usage

### As a library

``` python

from flipper_raw_rfid.rifl import Rifl
from flipper_raw_rfid.utils import pad_to_signal
import matplotlib.pyplot as plt 

rifl = Rifl.load('test/assets/Red354.ask.raw')
# Read the the raw pulse and duration values
pad = rifl.pulse_and_durations
# reconstructed binary signal
signal = pad_to_signal(pad)

plt.plot(signal[0:20000])

```

results in: 

![Plot of the RFID signal with matplotlib](docs/signal-plot.png)


There is also a short [tutorial notebook](docs/rifl-tutorial-1.ipynb)

### From commandline

``` bash
# Plot a file (requires matplotlib)
$ flipper-raw-rfid plot tests/assets/Red354.ask.raw
# Dump the contents in pad format (see below) 
$ flipper-raw-rfid convert --format=pad tests/assets/Red354.ask.raw Red354.pad.csv
# Dump the contents in signal format
$ flipper-raw-rfid convert --format=signal tests/assets/Red354.ask.raw Red354.signal.csv
```

#### Commandline help
```bash
flipper-raw-rfid --help
```
```
flipper-raw-rfid 

Description:
    Reads a raw rfid file from flipper zero and plots or converts the signal

Usage:
    flipper-raw-rfid convert [-f <format>] RAW_FILE [OUTPUT_FILE]
    flipper-raw-rfid plot RAW_FILE
    flipper-raw-rfid check RAW_FILE
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

Pulse and duration (pad) format:

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
``` 

# Tutorial

There is a short [RFID tutorial notebook](docs/rifl-tutorial-1.ipynb) to see if there is data in the recording and what to do with it.