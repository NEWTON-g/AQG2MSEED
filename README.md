# Script to generate mSEED from AQG .csv file

This script loads raw AQG data files and converts them to the seismological mSEED standard.

## Usage

Modify the input file in the `run.py` script and feed the `AQG2MSEED` convertor with an AQG file.

## Specifics

The sampling rate of the AQG is exactly 540ms but the computer clock may provide slightly different timestams. We assume that the sampling rate is precise, introducing some misfit between the converted and raw data. Data is split into continuous segments that are often bounded by recalibration pauses of the instrument every two hours. Each gap introduces a new data segment with a new start time. The traces are bundled in a stream and written to a mSEED file using ObsPy.

## Naming

The mSEED standard has four identifiers (ASCII, N bytes): network (2), station (5), location (2), and channel (3). The network is defined here as `2Q`, the station as `AQG`, the location is an empty string and will change when the AQG is moved. The channel is defined following the mSEED standard (M) because of the 2Hz sampling rate, (G) for gravimeter, and (Z) for the z-component. In total the identifier is `2Q.AQG..MGZ`.

## Channels

The convertor handles nine (if available) channels:

  * Raw vertical gravity (MGZ.D) - this is the absolute gravity value corrected for the AQG columns: quartz, tilt, pressure, syst, height, laser polarization. The tide has not been corrected and is left to the user. However, a tidal model is supplied for user convenience in the MXZ channel.
  * Earth tide (MXZ.D) including: solid earth tide, ocean loading, polar motion. This is the effect (not correction) and therefore needs to be subtracted from the gravity data.
  * Atmospheric pressure (MDO.D)
  * Sensor Head, Vacuum Chamber, Tiltmeter, External temperature (MK1, MK2, MK3, MK4)
  * X, and Y tilt (MA1.D, MA2.D)

The gain (sensitivity) to convert COUNTS to physical units is given in the metadata.

## Example

    >>> from obspy import read
    >>> st = read("2Q.AQG..MGZ.D.2020.192")
    >>> print(st)

    2 Trace(s) in Stream:
    2Q.AQG..MGZ | 2020-07-10T20:44:03.695000Z - 2020-07-10T22:42:34.415000Z | 1.9 Hz, 13169 samples
    2Q.AQG..MGZ | 2020-07-10T22:44:45.636000Z - 2020-07-10T23:59:59.496000Z | 1.9 Hz, 8360 samples
