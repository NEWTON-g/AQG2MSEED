import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import obspy

if __name__ == "__main__":

  for filename in os.listdir("data"):
  
    filepath = os.path.join("data", filename)

    df = pd.read_csv(filepath, parse_dates=[[1, 2]])
  
    x = df["date (utc)_time (utc)"]
    
    # These are all corrections to make to the absolute gravity measure
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
  
    plt.plot(x, y, color="green")
  
  # Read all converted mSEED data (and tidal model)
  st = obspy.read(os.path.join("mseed", "MGZ.D", "2Q.AQG..MGZ.D.2020.*"))
  st2 = obspy.read(os.path.join("mseed", "MXZ.D", "2Q.AQG..MXZ.D.2020.*"))
  
  # Subtract tidal model from AQG data
  for tr, tr2 in zip(st, st2):
    plt.plot(tr.times("matplotlib"), tr.data - tr2.data, color="red")
  
  plt.show()
