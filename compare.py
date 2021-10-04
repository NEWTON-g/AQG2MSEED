from obspy import read, UTCDateTime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("seaborn")

OFFSET = 9793798890

st = read("mseed/MGZ.D/*")

df = pd.read_csv("./data/capture_20210803_140132_raw_0.csv")

plt.plot(df["timestamp (s)"], df["raw vertical gravity (nm/s^2)"], label="AQG", color="green")

for tr in st:
  if tr == st[0]:
    plt.plot(tr.times("timestamp"), OFFSET + tr.data, label="mSEED")
  else:
    plt.plot(tr.times("timestamp"), OFFSET + tr.data)

plt.legend()

plt.show()
