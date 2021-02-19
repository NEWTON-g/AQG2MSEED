import os

from src.aqg2mseed import convert

if __name__ == "__main__":

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Columns to write to mSEED: each will be a channel
  columns = [
    "raw_gravity",
    "corrected_gravity",
    "atmospheric_pressure",
    "sensor_head_temperature",
    "vacuum_chamber_temperature",
    "tiltmeter_temperature",
    "x_tilt",
    "y_tilt"
  ]

  # Network identifier (NEWTON-g), station identifier (AQG), and location ("")
  network = "NG"
  station = "AQG"
  location = ""

  # Paths to (read, write) (from, to):
  path = "data"
  path2 = "mseed"

  for file in os.listdir(path):

    filepath = os.path.join(path, file)

    # Convert the input file to mSEED streams
    # Pass correct to add all gravity corrections
    files = convert(
      filepath,
      network,
      station,
      location,
      columns
    )

    # Write the streams to files
    for (filename, channel, stream) in files:

      print("Writing mSEED output file to %s." % filename)

      # Write to appropriate channel
      if not os.path.exists(os.path.join(path2, channel)):
        os.makedirs(os.path.join(path2, channel)) 

      stream.write(os.path.join(path2, channel, filename), format="MSEED")
