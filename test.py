from obspy import read, read_inventory
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

if __name__ == "__main__":

  """
  Function to test conversion of AQG data to mSEED
  """

  filepath = os.path.join("data", "capture_20200731_121217_raw_5.csv")
  df = pd.read_csv(filepath, parse_dates=[[1, 2]], float_precision='round_trip')

  inv = read_inventory("2Q.AQG.xml")
  
  tuples = [
    ("MK1.D", "sensor head temperature (°C)"),
    ("MK2.D", "vacuum chamber temperature (°C)"),
    ("MK3.D", "tiltmeter temperature (°C)"),
    ("MK4.D", "external temperature (°C)"),
    ("MA1.D", "X tilt (mrad)"),
    ("MA2.D", "Y tilt (mrad)"),
    ("MDO.D", "atmospheric pressure (hPa)")
  ]
  
  for (channel, column) in tuples:

    try:
      stream = read(os.path.join("mseed", channel, "2Q.AQG..%s.2020.218" % channel))
    except:
      continue
  
    stream.remove_sensitivity(inv)
    
    for trace in stream:
      plt.plot(trace.times("matplotlib"), trace.data, color="grey")
    
    plt.title(channel)
    plt.plot(df["date (utc)_time (utc)"], df[column])
    plt.show()

  # Gravity is separate and has some corrections already applied
  MGZ = read(os.path.join("mseed", "MGZ.D", "2Q.AQG..MGZ.D.2020.218"))
  MXZ = read(os.path.join("mseed", "MXZ.D", "2Q.AQG..MXZ.D.2020.218"))

  # Conver to M/S**2 (gain is equal to 1; already stored in M/S**2)
  MGZ.remove_sensitivity(inv)
  MXZ.remove_sensitivity(inv)

  # Correct and plot
  for (gravity, tide) in zip(MGZ, MXZ):
    plt.plot(gravity.times("matplotlib"), (gravity.data - tide.data), color="grey")

  y = df["raw vertical gravity (nm/s^2)"]
  y -= df["delta_g_quartz (nm/s^2)"]
  y -= df["delta_g_tilt (nm/s^2)"]
  y -= df["delta_g_pressure (nm/s^2)"]
  y -= df["delta_g_syst (nm/s^2)"]
  y -= df["delta_g_height (nm/s^2)"]
  y -= df["delta_g_laser_polarization (nm/s^2)"]
  y -= df["delta_g_earth_tide (nm/s^2)"]
  y -= df["delta_g_ocean_loading (nm/s^2)"]
  y -= df["delta_g_polar (nm/s^2)"]

  # Plot in M/S**2 (from nm/s**2 -> m/s**2)
  plt.plot(df["date (utc)_time (utc)"], 1E-9 * y)
  plt.show()
  plt.close()
