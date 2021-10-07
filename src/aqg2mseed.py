import datetime
import numpy as np
import obspy
import pandas as pd

class AQG2MSEED():

  """
  Class to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, KNMI
  Last Updated: Oct. 2021
  """

  # The AQG samples precisely at 540ms (given a 0.01s of tolerance)
  # This does not exactly match the timestamp in the raw AQG data because of clock drift / timing but it averages out (see fig. clockdrift.png)
  SAMPLING_INT = 0.540
  EPSILON = 0.01

  # Offset to be able to use STEIM2 effectively (which is unfortunately limited to 32-bit differences)
  GRAV_OFFSET = 9793798890
  QUALITY = "D"


  def __init__(self, network, station, location):

    """
    def AQG2MSEED.__init__
    Initializes the converter: requires a SEED network, station, and location code
    """

    self.network = network
    self.station = station
    self.location = location


  def get_header(self, starttime, channel):

    """
    def AQG2MSEED.get_header
    Returns a new dictionary representing the SEED header that is used by ObsPy
    """

    # Define the mSEED header
    # Sampling rate should be rounded to 6 decimals.. floating point issues
    return dict({
      "starttime": starttime,
      "network": self.network,
      "station": self.station,
      "location": self.location,
      "channel": channel,
      "mseed": {"dataquality": self.QUALITY},
      "sampling_rate": np.round(1. / self.SAMPLING_INT, decimals=8)
    })


  def map_name(self, name):
  
    """
    def AQG2MSEED.map_name
    Maps an input name to a tuple (gain, dataframe entry, and mSEED channel code)
    
    mSEED channel codes have three identifiers: 
      1. Sampling rate (M) for medium
      2. Instrument identifier (G) gravimeter, (D) barometer, (M) thermometer, (A) tilt
      3. Component (Z) vertical, (N) north, (E) east, (1 .. N) arbitrary numbering
    Refer to the mSEED manual
    """
  
    # Gravity codes: quality code will be different
    if name == "raw vertical gravity (nm/s^2)":
      return (1E0, "MGZ")
    # Pressure codes
    elif name == "atmospheric pressure (hPa)":
      return (1E3, "MDO")

    # Tides
    elif name == "delta_g_earth_tide (nm/s^2)":
      return (1E0, "MXZ")
  
    # Temperature codes
    elif name == "sensor head temperature (°C)":
      return (1E3, "MK1")
    elif name == "vacuum chamber temperature (°C)":
      return (1E3, "MK2")
    elif name == "tiltmeter temperature (°C)":
      return (1E3, "MK3")
    elif name == "external temperature (°C)":
      return (1E3, "MK4")
  
    # Tilting is X, Y not North and East
    elif name == "X tilt (mrad)":
      return (1E3, "MA1")
    elif name == "Y tilt (mrad)":
      return (1E3, "MA2")
  
    else:
      raise ValueError("Invalid field %s requested." % name)
  

  def add_trace(self, stream, timestamps, data, start, end, channel):

    """
    def AQG2MSEED.add_trace
    Adds a trace to the passed stream based on the start and end incides
    """

    # Cut off the right slice
    samples = data[start:end].astype("int32")

    # mSEED record header
    header = self.get_header(obspy.UTCDateTime(timestamps[start]), channel)
    trace = obspy.Trace(samples, header=header)

    print("Adding trace [%s]." % trace)

    # Report the timing mismatch due to irregular sampling

    if end is None:
      mismatch = obspy.UTCDateTime(timestamps.iloc[-1]) - trace.stats.endtime
    else:
      mismatch = obspy.UTCDateTime(timestamps.iloc[end - 1]) - trace.stats.endtime

    print("The current trace endtime mismatch is %.3fs." % np.abs(mismatch))

    stream.append(trace)

    # Return simple checksum
    return np.bitwise_xor.reduce(samples)


  def get_tide(self, df):

    """
    def AQG2MSEED.get_tide
    Returns the contribution of all tidal corrections (ocean loading, polar motion, solid earth)
    """

    return np.array(df["delta_g_earth_tide (nm/s^2)"], dtype="int64") + \
           np.array(df["delta_g_ocean_loading (nm/s^2)"], dtype="int64") + \
           np.array(df["delta_g_polar (nm/s^2)"], dtype="int64")


  def correct_data(self, df, data):

    """
    def AQG2MSEED.correct_data
    Corrects the gravitydata for all effects (tides not included)
    """

    # Apply all these corrections
    # We avoid these corrections: delta_g_earth_tide (nm/s^2), delta_g_ocean_loading (nm/s^2) , delta_g_polar (nm/s^2)
    # These are kept in a different MXZ channel if research want them (or calculate themselves)
    for correction in ("delta_g_quartz (nm/s^2)",
                       "delta_g_tilt (nm/s^2)",
                       "delta_g_pressure (nm/s^2)",
                       "delta_g_syst (nm/s^2)",
                       "delta_g_height (nm/s^2)",
                       "delta_g_laser_polarization (nm/s^2)"):
      data -= np.array(df[correction], dtype="int64")


  def to_files(self, files, channel, stream):

      """
      def AQG2MSEED.to_files
      Converts streams to mSEED files
      """

      # Here we will sort the streams
      # Seismological data is conventionally stored in daily files
      # Therefore, we will loop over all days between the start and the end date
      start_date = obspy.UTCDateTime(stream[0].stats.starttime.date)
      end_date = obspy.UTCDateTime(stream[-1].stats.starttime.date)
 
      print("Added a total of %d traces." % len(stream))
      print("Adding traces to the respective day files.")
 
      # One problem here is that if one day if spread in two files it overwrites the first file
      while(start_date <= end_date):
 
        # Filename is network, station, location, channel, quality (D), year, day of year delimited by a period
        filename = ".".join([
          self.network,
          self.station,
          self.location,
          channel,
          self.QUALITY,
          start_date.strftime("%Y"),
          start_date.strftime("%j")
        ])
 
        # Get the data beloning to a single day and write to the correct file
        st_day = stream.slice(start_date, start_date + datetime.timedelta(days=1))
        files.append((filename, channel + "." + self.QUALITY, st_day))
 
        # Increment the day
        start_date += datetime.timedelta(days=1)


  def get_continuous_traces(self, timestamps):

    """
    def AQG2MSEED.get_continuous_traces
    Returns the indices of all end points of the continuous traces
    """

    # Get the true sampling interval between the samples to identify gaps
    differences = np.diff(timestamps)

    # Check whether the sampling interval is within a tolerance: otherwise we create a reference
    # to the index where the gap is. We will use these indices to create individual traces.
    indices = np.flatnonzero(
      (differences > (self.SAMPLING_INT + self.EPSILON)) |
      (differences < (self.SAMPLING_INT - self.EPSILON))
    )

    # Add one to split on the correct sample since np.diff reduced the index by one
    indices += 1

    # Add final index because the final trace ends there..
    return np.append(indices, len(timestamps))


  def add_stream(self, files, df, name):

    """
    def AQG2MSEED.add_stream
    Adds a stream (channel) to the output
    """

    # Reference the timestamp for convenience 
    timestamps = df["timestamp (s)"].astype("float64")
 
    indices = self.get_continuous_traces(timestamps)

    # Create an empty ObsPy stream to collect all traces
    stream = obspy.Stream()

    # Map the requested data file
    (gain, channel) = self.map_name(name)
 
    # Tide channel
    if channel == "MXZ":
      data = self.get_tide(df)

    else:
      # Fetch the data
      data = np.array(gain * df[name], dtype="int64")

      # Special handling for gravity
      if channel == "MGZ":

        # All sorts of corrections
        if True:
          self.correct_data(df, data)

        # Subtract an offset to keep values in 32-bit range
        data -= self.GRAV_OFFSET

    # Here we start collecting the pandas data frame in to continuous traces without gaps
    # The index of the first trace is naturally 0
    start = 0
    checksum = np.bitwise_xor.reduce(data)

    # Go over the collected indices where there is a gap!
    for end in list(indices):

      # Alert client of the gap size
      print("Found gap in data outside of tolerance of length.")

      # Bitwise xor to bring checksum back to 0
      checksum ^= self.add_trace(stream, timestamps, data, start, end, channel)

      # Set the start to the end of the previous trace and proceed with the next trace
      start = end

    if checksum != 0:
      raise AssertionError("Data checksum is invalid. Not all samples were written.")

    # Add to the file collection
    self.to_files(files, channel, stream)


  def convert(self, filename, names):
  
    """
    def AQG2MSEED.convert
    Converts a file and the requested channels to mSEED files: returns an array of ObsPy streams ready for writing
    """
  
    print("Reading AQG input file %s." % filename)
  
    # Collection of files to return after conversion
    files = list()

    # Read the supplied AQG datafile to a pandas dataframe
    try:
      df = pd.read_csv(filename, parse_dates=[0])
    except Exception:
      return files
  
    # Go over all the requested channels
    for name in names:
      if name in df:
        self.add_stream(files, df, name)

    return files
