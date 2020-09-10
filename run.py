from src.aqg2mseed import convert

if __name__ == "__main__":

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Column to write to mSEED
  column = "raw_gravity"
  # Network identifier (NEWTON-g), station identifier (AQG), and location ("")
  network = "NG"
  station = "AQG"
  location = ""

  # Convert the input file to mSEED streams
  files = convert(
    "data/capture_20200826_170834_raw_13.csv",
    network,
    station,
    location,
    column
  )

  # Write the streams to files
  for (filename, stream) in files:

    print("Writing mSEED output file to %s." % filename)

    stream.write(filename, format="MSEED")
