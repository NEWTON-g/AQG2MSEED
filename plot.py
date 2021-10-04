from obspy import read, read_inventory
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os

plt.style.use("seaborn")

channels = os.listdir("mseed")
fig, axs = plt.subplots(len(channels), 1, sharex=True)
inventory = read_inventory("2Q.AQG.xml")

for ax, channel in zip(axs, channels):
  st = read(os.path.join("mseed", channel, "*"))
  st.merge(fill_value="interpolate")
  #st.remove_sensitivity(inventory)
  #st.detrend(type="polynomial", order=2)
  #st.filter("lowpass", freq=0.001)
  ax.plot(st[0].times("matplotlib"), st[0].data, label=channel)
  ax.legend(loc="upper right", frameon=True)

plt.tight_layout()
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
plt.gca().xaxis.set_major_locator(mdates.HourLocator())
plt.show()
  
