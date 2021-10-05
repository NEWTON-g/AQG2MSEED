import os

from src.aqg2mseed import AQG2MSEED

if __name__ == "__main__":

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Columns to write to mSEED: each will be a channel
  columns = [
    "raw vertical gravity (nm/s^2)",
    #"atmospheric pressure (hPa)"
    #"sensor head temperature (°C)",
    #"vacuum chamber temperature (°C)",
    #"tiltmeter temperature (°C)",
    #"external temperature (°C)",
    #"X tilt (mrad)",
    #"Y tilt (mrad)"
  ]

  # These are the SEED network, station identifiers. Location remains blank.
  # See https://www.fdsn.org/networks/detail/2Q_2020/
  convertor = AQG2MSEED("2Q", "AQG", "")

  # Paths to (read, write) (from, to):
  path = "data"
  path2 = "mseed"

  for file in os.listdir(path):

    filepath = os.path.join(path, file)

    # Convert the input file to mSEED streams
    # Pass correct to add all gravity corrections
    files = convertor.convert(filepath, columns)

    # Write the streams to files
    for (filename, channel, stream) in files:

      print("Writing mSEED output file to %s." % filename)

      # Write to appropriate channel
      if not os.path.exists(os.path.join(path2, channel)):
        os.makedirs(os.path.join(path2, channel)) 

      stream.write(os.path.join(path2, channel, filename), format="MSEED")
