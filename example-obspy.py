from obspy import read, read_inventory

def show(inventory, stream):

  # Have to remove the sensitivity to go to proper units
  stream.remove_sensitivity(inventory)

  stream.plot()

if __name__ == "__main__":

  # Metadata
  inventory = read_inventory("2Q.AQG.xml")

  # Read gravity channel
  grav = read("mseed/MGZ.D/2Q.AQG..MGZ.D.2021.215")
  show(inventory, grav)

  # Read temperature channel
  temp = read("mseed/MK1.D/2Q.AQG..MK1.D.2021.215")
  show(inventory, temp)

  # Read tilt channel
  temp = read("mseed/MA1.D/2Q.AQG..MA1.D.2021.215")
  show(inventory, temp)
