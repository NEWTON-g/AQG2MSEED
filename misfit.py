from obspy import read, UTCDateTime
import datetime
import matplotlib.dates as mdates
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("seaborn")
plt.title("AQG Capture_20210803_140132_raw_0.csv\nDifference between recorded timestamp and inferred timestamp from trace start and 540ms sample intervals")

st = read("mseed/MGZ.D/*")

df = pd.read_csv("./data/capture_20210803_140132_raw_0.csv")
diff = np.diff(df["timestamp (s)"])
idx = np.flatnonzero(diff > 1.0)
idx += 1
start = 0
for j, i in enumerate(idx):
  sl = diff[start:i - 1]
  dk = df["timestamp (s)"][start:i - 1]
  dates=[datetime.datetime.fromtimestamp(ts) for ts in dk]
  if j != 0:
    plt.gca().axvspan(prev[-1], dates[0], alpha=0.25, color="red", label="Gap" if j == 1 else "")
  start = i 
  plt.plot(dates, np.cumsum(sl) - 0.540 * np.arange(1, len(sl) + 1), color="grey", label="Drift" if j == 1 else "")
  prev = dates


plt.ylabel("Timestamp Drift (s)")
plt.xlabel("Timestamp")
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gca().xaxis.set_major_locator(mdates.HourLocator())
plt.legend(frameon=True)
plt.tight_layout()
plt.savefig("clockdrift.png", bbox_inches="tight", dpi=300)
