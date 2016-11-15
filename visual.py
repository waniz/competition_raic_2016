import matplotlib.pyplot as plt
import numpy as np

plt.style.use('ggplot')


plt.xlim(0, -4000)
plt.ylim(-4000, 0)

x = [-1370, -50, -350, -2312, -400, -1929, -902]
y = [-3650, -2693, -1656, -3950, -3600, -2400, -2768]
area = np.pi * (5 ** 2)
plt.scatter(x, y, s=area, color='green')

plt.xlim(0, -4000)
plt.ylim(-4000, 0)

x = [-3600, -2630, -3950, -3650, -1688, -2071, -3098]
y = [-400, -350, -1307, -2344, -50, -1600, -1232]
area = np.pi * (5 ** 2)
plt.scatter(x, y, s=area, color='red')

map_size = 4000
waypoints_path = []
waypoints_path.append([100, map_size - 100])
waypoints_path.append([100, map_size - 400])
waypoints_path.append([200, map_size - 800])
waypoints_path.append([200, map_size * 0.75])
waypoints_path.append([200, map_size * 0.5])
waypoints_path.append([200, map_size * 0.25])
waypoints_path.append([200, 200])
waypoints_path.append([map_size * 0.25, 200])
waypoints_path.append([map_size * 0.5, 200])
waypoints_path.append([map_size * 0.75, 190])
waypoints_path.append([map_size - 200, 200])

x, y = [], []
for waypoint in waypoints_path:
    x.append(-waypoint[0])
    y.append(-waypoint[1])
plt.scatter(x, y, color='blue')
plt.xlim(0, -4000)
plt.ylim(-4000, 0)

waypoints_path = []
waypoints_path.append([map_size - 100, 100])
waypoints_path.append([map_size - 400, 100])
waypoints_path.append([map_size - 800, 200])
waypoints_path.append([map_size * 0.75, 200])
waypoints_path.append([map_size * 0.5, 200])
waypoints_path.append([map_size * 0.25, 200])
waypoints_path.append([200, 200])
waypoints_path.append([200, map_size * 0.25])
waypoints_path.append([200, map_size * 0.5])
waypoints_path.append([190, map_size * 0.75])
waypoints_path.append([200, map_size - 200])

x, y = [], []
for waypoint in waypoints_path:
    x.append(-waypoint[0])
    y.append(-waypoint[1])
plt.scatter(x, y, color='orange')
plt.xlim(0, -4000)
plt.ylim(-4000, 0)

plt.show()
