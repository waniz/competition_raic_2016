import matplotlib.pyplot as plt

plt.style.use('ggplot')


plt.xlim(0, -4000)
plt.ylim(-4000, 0)

x = [-1370, -50, -350, -2312, -400, -1929, -902]
y = [-3650, -2693, -1656, -3950, -3600, -2400, -2768]

plt.scatter(x, y)
plt.show()

map_size = 4000
waypoints = []

waypoints.append([100, map_size - 100])
waypoints.append([100, map_size - 400])
waypoints.append([200, map_size - 800])
waypoints.append([200, map_size * 0.75])
waypoints.append([200, map_size * 0.5])
waypoints.append([200, map_size * 0.25])
waypoints.append([200, 200])
waypoints.append([map_size * 0.25, 200])
waypoints.append([map_size * 0.5, 200])
waypoints.append([map_size * 0.75, 200])
waypoints.append([map_size - 200, 200])

x, y = [], []
for waypoint in waypoints:
    x.append(-waypoint[0])
    y.append(-waypoint[1])
plt.scatter(x, y)
plt.xlim(0, -4000)
plt.ylim(-4000, 0)
plt.show()
