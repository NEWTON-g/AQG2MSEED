from obspy import read, read_inventory

def show(inventory, stream):

  # Have to remove the sensitivity to go to proper units
  stream.remove_sensitivity(inventory)

  stream.plot()

if __name__ == "__main__":

  # Metadata
  inventory = read_inventory("NG.AQG.xml")

  # Read gravity channel
  grav = read("mseed/MGZ/NG.AQG..MGZ.D.2020.213")
  show(inventory, grav)

  # Read temperature channel
  temp = read("mseed/MK1/NG.AQG..MK1.D.2020.213")
  show(inventory, temp)

  # Read tilt channel
  temp = read("mseed/MA1/NG.AQG..MA1.D.2020.213")
  show(inventory, temp)
