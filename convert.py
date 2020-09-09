import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import obspy

if __name__ == "__main__":

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Sampling interval tolerance (s)
  EPSILON = 0.01
  # The AQG samples at 0.54 seconds instead of 2Hz
  SAMPLING_INT = 0.54

  filename = "capture_20200826_170834_raw_13.csv"

  print("Reading AQG input file %s." % filename)

  # Read the supplied AQG datafile to a dataframe
  df = pd.read_csv(filename, usecols=[0,6])

  # Define the mSEED header
  header = dict({
    "starttime": None,
    "network": "NG",
    "station": "AQG",
    "location": "",
    "channel": "MGZ",
    "sampling_rate": (1. / SAMPLING_INT)
  })

  # Extract the start year and day from the first available timestamp
  timestamp = obspy.UTCDateTime(df["timestamp (s)"][0])

  # Get the true sampling interval between the samples to identify gaps
  differences = np.diff(df["timestamp (s)"])

  # Check whether the sampling interval is within a tolerance: otherwise we create a new trace
  indices = np.flatnonzero(
    (differences < (SAMPLING_INT - EPSILON)) |
    (differences > (SAMPLING_INT + EPSILON))
  )

  # Add one to split on the correct sample since np.diff reduced the index by one
  indices += 1
  
  # Create an empty ObsPy stream
  st = obspy.Stream()
  
  # Reference the data and convert to float64 for easy of access
  data = np.array(df["raw vertical gravity (nm/s^2)"], dtype="float64")

  # Index of the first trace
  start = 0

  # Add none to the final index to include the final trace
  for end in list(indices):

    print("Found gap in data outside of tolerance of length: %.3fs. Starting new trace." % differences[end - 1])

    # Set the start time of the trace equal to the first sample of the trace
    header["starttime"] = obspy.UTCDateTime(df["timestamp (s)"][start])

    # Get the slice between start & end and add it to the existing stream
    tr = obspy.Trace(data[start:end], header=header)

    print("Adding trace [%s]." % tr)

    # Report the mismatch
    mismatch = obspy.UTCDateTime(df["timestamp (s)"][end - 1]) - tr.stats.endtime
    print("The trace endtime mismatch is %.3fs." % np.abs(mismatch))

    # Save the trace to the stream
    st.append(tr)

    # Set the start to the end of the previous trace
    start = end

  # Append the remaining trace: wrap this in a function
  header["starttime"] = obspy.UTCDateTime(df["timestamp (s)"][start])
  tr = obspy.Trace(data[start:], header=header)
  mismatch = obspy.UTCDateTime(df["timestamp (s)"][end - 1]) - tr.stats.endtime
  print("Adding remaining trace [%s]." % tr)
  print("The current trace endtime mismatch is %.3fs." % np.abs(mismatch))
  st.append(tr)
  
  # Data is stored in daily files
  start_date = obspy.UTCDateTime(st[0].stats.starttime.date)
  end_date = obspy.UTCDateTime(st[-1].stats.starttime.date)

  while(start_date <= end_date):

    # Filename is network, station, location, channel, quality (D), year, day of year delimited by a period
    filename = ".".join([
      header["network"],
      header["station"],
      header["location"],
      header["channel"],
      "D",
      start_date.strftime("%Y"),
      start_date.strftime("%j")
    ])

    print("Writing mSEED output file to %s." % filename)

    # Get the data beloning to a single day and write to file
    st_day = st.slice(start_date, start_date + datetime.timedelta(days=1))
    st_day.write(filename, format="MSEED")

    # Increment the day
    start_date += datetime.timedelta(days=1)
