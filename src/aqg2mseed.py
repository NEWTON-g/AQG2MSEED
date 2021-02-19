import pandas as pd
import datetime
import numpy as np
import obspy

def map_name(name):

  """
  def map_name
  Maps an input name to a tuple (column, dataframe entry, and mSEED channel code)
  
  mSEED channel codes have three identifiers: 
    1. Sampling rate (M) for medium
    2. Instrument identifier (G) gravimeter, (D) barometer, (M) thermometer, (A) tilt
    3. Component (Z) vertical, (N) north, (E) east, (1 .. N) arbitrary numbering
  Refer to the mSEED manual
  """

  # Gravity codes
  if name == "raw_gravity":
    return ("raw vertical gravity (nm/s^2)", "MGZ")
  # Pressure codes
  elif name == "atmospheric_pressure":
    return ("atmospheric pressure (hPa)", "MDO")

  # Temperature codes
  elif name == "sensor_head_temperature":
    return ("sensor head temperature (°C)", "MK1")
  elif name == "vacuum_chamber_temperature":
    return ("vacuum chamber temperature (°C)", "MK2")
  elif name == "tiltmeter_temperature":
    return ("tiltmeter temperature (°C)", "MK3")

  # Tilting is X, Y not North and East
  elif name == "x_tilt":
    return ("X tilt (mrad)", "MA1")
  elif name == "y_tilt":
    return ("Y tilt (mrad)", "MA2")

  else:
    raise ValueError("Invalid field %s requested." % name)

def convert(filename, network, station, location, names, correct=False):

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Sampling interval tolerance (s)
  EPSILON = 0.01
  # The AQG samples at 0.54 seconds instead of 2Hz
  SAMPLING_INT = 0.54

  print("Reading AQG input file %s." % filename)

  # Read the supplied AQG datafile to a dataframe.
  # We use the timestamp (0) and the requested column index (see map_name)
  df = pd.read_csv(filename)

  # Reference the timestamp for convenience 
  timestamps = df["timestamp (s)"]

  # Get the true sampling interval between the samples to identify gaps
  differences = np.diff(timestamps)

  # Check whether the sampling interval is within a tolerance: otherwise we create a reference
  # to the index where the gap is. We will use these indices to create individual traces.
  indices = np.flatnonzero(
    (differences < (SAMPLING_INT - EPSILON)) |
    (differences > (SAMPLING_INT + EPSILON))
  )

  # Add one to split on the correct sample since np.diff reduced the index by one
  indices += 1
  
  # Collection of files to return after conversion
  files = list()

  # Go over all the requested channels
  for name in names:

    # Create an empty ObsPy stream to collect all traces
    st = obspy.Stream()

    # Map the requested data file
    (column, channel) = map_name(name)

    # Define the mSEED header
    # Sampling rate should be rounded to 6 decimals.. floating point issues
    header = dict({
      "starttime": None,
      "network": network,
      "station": station,
      "location": location,
      "channel": channel,
      "sampling_rate": np.round((1. / SAMPLING_INT), 6)
    })

    # Reference the data and convert to int64 for storage. mSEED cannot store long long (64-bit) integers.
    # Can we think of a clever trick? STEIM2 compression (factor 3) is available for integers, not for ints.
    if name == "raw_gravity":
      data = np.array(df[column], dtype="int64")

    # Scale auxilliary ints to integer by multiplying by 1000 (this is corrected for in the sensor metadata)
    elif name in ("atmospheric_pressure",
                  "sensor_head_temperature",
                  "vacuum_chamber_temperature",
                  "tiltmeter_temperature",
                  "x_tilt",
                  "y_tilt"):
      data = np.array(1E3 * df[column], dtype="int32")

    else:
      raise ValueError("Unknown column requested.")

    # Make delta gravity corrections if requested
    if name == "raw_gravity" and correct:
      # Correct for all these columns!
      for correction in ("delta_g_quartz (nm/s^2)",
                         "delta_g_tilt (nm/s^2)",
                         "delta_g_pressure (nm/s^2)",
                         "delta_g_earth_tide (nm/s^2)",
                         "delta_g_ocean_loading (nm/s^2)",
                         "delta_g_polar (nm/s^2)",
                         "delta_g_syst (nm/s^2)",
                         "delta_g_height (nm/s^2)",
                         "delta_g_laser_polarization (nm/s^2)"):
        data -= np.array(df[correction], dtype="int64")

    # Calculate the bitwise xor of all gravity data samples as checksum
    # After writing to mSEED, we apply xor again and the result should come down to 0 
    checksum = np.bitwise_xor.reduce(data)

    # Here we start collecting the pandas data frame in to continuous traces without gaps
    # The index of the first trace is naturally 0
    start = 0

    # Go over the collected indices where there is a gap!
    for end in list(indices):

      # Alert client of the gap size
      print("Found gap in data outside of tolerance of length: %.3fs. Starting new trace." % differences[end - 1])

      # Set the start time of the trace equal to the first sample of the trace
      header["starttime"] = obspy.UTCDateTime(timestamps[start])

      # Get the array slice between start & end and add it to the existing stream
      tr = obspy.Trace(data[start:end].astype("float64"), header=header)

      print("Adding trace [%s]." % tr)

      # Report the timing mismatch due to irregular sampling
      mismatch = obspy.UTCDateTime(timestamps[end - 1]) - tr.stats.endtime
      print("The trace endtime mismatch is %.3fs." % np.abs(mismatch))

      # XOR with the existing checksum: eventually this should reduce back to 0
      checksum ^= np.bitwise_xor.reduce(tr.data.astype("int64"))

      # Save the trace to the stream
      st.append(tr)

      # Set the start to the end of the previous trace and proceed with the next trace
      start = end

    # Remember to append the remaining trace after the last gap
    # This does not happen automatically but is the same procedure as inside the while loop
    header["starttime"] = obspy.UTCDateTime(timestamps[start])
    tr = obspy.Trace(data[start:].astype("float64"), header=header)
    mismatch = obspy.UTCDateTime(timestamps[len(timestamps) - 1]) - tr.stats.endtime
    print("Adding remaining trace [%s]." % tr)
    print("The current trace endtime mismatch is %.3fs." % np.abs(mismatch))
    st.append(tr)

    # Add the checksum of the final trace
    checksum ^= np.bitwise_xor.reduce(tr.data.astype("int64"))
    
    # Confirm that the checksum is zero and therefore correct
    if checksum != 0:
      raise AssertionError("Data xor checksum is incorrect! Not all samples were written correctly.")

    # Here we will sort the streams
    # Seismological data is conventionally stored in daily files
    # Therefore, we will loop over all days between the start and the end date
    start_date = obspy.UTCDateTime(st[0].stats.starttime.date)
    end_date = obspy.UTCDateTime(st[-1].stats.starttime.date)

    print("Added a total of %d traces." % len(st))
    print("Adding traces to the respective day files.")

    # One problem here is that if one day if spread in two files it overwrites the first file
    while(start_date <= end_date):

      # Filename is network, station, location, channel, quality (D), year, day of year delimited by a period
      filename = ".".join([
        header["network"],
        header["station"],
        header["location"],
        header["channel"],
        "Q",
        start_date.strftime("%Y"),
        start_date.strftime("%j")
      ])

      # Get the data beloning to a single day and write to the correct file
      st_day = st.slice(start_date, start_date + datetime.timedelta(days=1))
      files.append((filename, channel, st_day))

      # Increment the day
      start_date += datetime.timedelta(days=1)

  # Ready for saving to disk!
  return files
