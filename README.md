# Flipper Zero Raw RFID Tools

A python library for reading and analyzing Flipper Zero raw RFID files (`tag.[ap]sk.raw`)
 * [Installation](#installation)

    <!-- * [Via pip](#via-pip) -->
    * [From source](#from-source)
 * [Usage](#usage)
 
## Installation

<!--

### Via pip

```bash
pip install flipper-raw-rfid
```
-->

### From source
```bash
git clone https://github.com/hnesk/flipper-raw-rfid.git 
cd flipper-raw-rfid
make install
```


## Usage

### As a library

``` python

from flipper_raw_rfid import RiflFile
import matplotlib.pyplot as plt 


with RiflFile.open('test/assets/Red354.ask.raw') as rifl:
     # for the reconstructed binary signal
     signal = rifl.signal()
     # or for the raw pulse and duration values
     pd = rifl.pulse_and_durations()

plt.plot(signal[0:20000])

```
