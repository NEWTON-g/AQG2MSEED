# Script to generate mSEED from AQG .csv file

This script loads raw AQG data files and converts them to the seismological mSEED standard.

## Usage
Modify the input file in the `run.py` script. An example AQG input file is given: `capture_20200826_170834_raw_13.csv` that is written to `2Q.AQG..MGZ.D.2021.215`.

## Specifics

The sampling rate of the AQG is exactly 540ms but the computer clock may provide slightly different timestams. We assume that the sampling rate is precise, introducing some misfit between the converted and raw data (fig. clockdrift.png). Data is split into continuous segments that are often bounded by recalibration pauses of the instrument every two hours. Each gap introduces a new data segment with a new start time. The traces are bundled in a stream and written to a mSEED file using ObsPy.

## Naming

The mSEED standard has four identifiers (ASCII, N bytes): network (2), station (5), location (2), and channel (3). The network is defined here as `2Q`, the station as `AQG`, the location is an empty string and will change when the AQG is moved. The channel is defined following the mSEED standard (M) because of the 2Hz sampling rate, (G) for gravimeter, and (Z) for the z-component. In total the identifier is `2Q.AQG..MGZ`.

## Example

    >>> from obspy import read
    >>> st = read("2Q.AQG..MGZ.D.2020.215")
    >>> print(st)

    6 Trace(s) in Stream:
    2Q.AQG..MGZ | 2021-08-03T14:01:32.279000Z - 2021-08-03T15:12:07.499000Z | 1.9 Hz, 7844 samples
    2Q.AQG..MGZ | 2021-08-03T15:13:45.591000Z - 2021-08-03T15:14:48.771000Z | 1.9 Hz, 118 samples
    2Q.AQG..MGZ | 2021-08-03T15:15:28.189000Z - 2021-08-03T17:13:41.089000Z | 1.9 Hz, 13136 samples
    2Q.AQG..MGZ | 2021-08-03T17:15:55.632000Z - 2021-08-03T19:15:15.492000Z | 1.9 Hz, 13260 samples
    2Q.AQG..MGZ | 2021-08-03T19:17:28.892000Z - 2021-08-03T21:16:48.212000Z | 1.9 Hz, 13259 samples
    2Q.AQG..MGZ | 2021-08-03T21:19:02.150000Z - 2021-08-03T23:18:22.550000Z | 1.9 Hz, 13261 samples

![Example Stream](images/plot.png)
