from src.aqg2mseed import convert

if __name__ == "__main__":

  """
  Script to convert AQG gravimeter data to mSEED using ObsPy
  Author: Mathijs Koymans, 2020
  """

  # Column to write to mSEED
  name = "raw_gravity"

  # Convert the input file to 
  files = convert("data/capture_20200826_170834_raw_13.csv", "NG", "AQG", "", name)

  for (filename, stream) in files:

    print("Writing mSEED output file to %s." % filename)

    stream.write(filename, format="MSEED")
