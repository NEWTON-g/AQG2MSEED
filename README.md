# Script to generate mSEED from AQG .csv file

Modify the input file in the `run.py` script. An example AQG input file is given: `capture_20200826_170834_raw_13.csv`.

## Specifics

The sampling rate of the AQG appears to be 0.54s. The ObsPy library is used to write mSEED files. Data is split in to continuous segments (a full trace without gaps). Each gap (with some tolerance due to irregular sampling of the AQG) introduces a new data segment with a new start time. The traces are bundled in a stream and written to a mSEED file.

## Naming

The mSEED standard has four identifiers (ASCII, N bytes): network (2), station (5), location (2), and channel (3). The network is defined here as `NG`, the station as `AQG`, the location is an empty string and will change when the AQG is moved. The channel is defined following the mSEED standard (M) because of the 2Hz sampling rate, (G) for gravimeter, and (Z) for the z-component. In total the identifier is `NG.AQG..MGZ`.
