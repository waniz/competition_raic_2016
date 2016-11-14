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
waypoints_path.append([150, map_size - 500])
waypoints_path.append([160, map_size - 600])
waypoints_path.append([180, map_size - 700])
waypoints_path.append([200, map_size - 800])
waypoints_path.append([200, map_size - 900])
waypoints_path.append([210, map_size * 0.75])
waypoints_path.append([230, map_size * 0.7])
waypoints_path.append([240, map_size * 0.67])
waypoints_path.append([230, map_size * 0.625])
waypoints_path.append([220, map_size * 0.58])
waypoints_path.append([215, map_size * 0.55])
waypoints_path.append([200, map_size * 0.5])
waypoints_path.append([200, map_size * 0.45])
waypoints_path.append([200, map_size * 0.4])
waypoints_path.append([200, map_size * 0.35])
waypoints_path.append([200, map_size * 0.3])
waypoints_path.append([200, map_size * 0.25])

waypoints_path.append([200, 900])
waypoints_path.append([200, 800])
waypoints_path.append([200, 700])
waypoints_path.append([180, 600])
waypoints_path.append([200, 500])
waypoints_path.append([220, 400])
waypoints_path.append([190, 300])
waypoints_path.append([200, 200])

waypoints_path.append([300, 210])
waypoints_path.append([400, 190])
waypoints_path.append([500, 210])
waypoints_path.append([600, 190])
waypoints_path.append([700, 210])
waypoints_path.append([800, 190])
waypoints_path.append([900, 210])
waypoints_path.append([map_size * 0.25, 210])
waypoints_path.append([map_size * 0.28, 190])
waypoints_path.append([map_size * 0.31, 210])
waypoints_path.append([map_size * 0.34, 190])
waypoints_path.append([map_size * 0.37, 210])
waypoints_path.append([map_size * 0.4, 190])
waypoints_path.append([map_size * 0.43, 210])
waypoints_path.append([map_size * 0.47, 190])
waypoints_path.append([map_size * 0.53, 210])
waypoints_path.append([map_size * 0.56, 190])
waypoints_path.append([map_size * 0.59, 210])
waypoints_path.append([map_size * 0.62, 190])
waypoints_path.append([map_size * 0.65, 210])
waypoints_path.append([map_size * 0.68, 190])
waypoints_path.append([map_size * 0.71, 210])
waypoints_path.append([map_size * 0.75, 190])

waypoints_path.append([map_size - 900, 210])
waypoints_path.append([map_size - 800, 200])
waypoints_path.append([map_size - 700, 200])
waypoints_path.append([map_size - 600, 200])
waypoints_path.append([map_size - 500, 200])

waypoints_path.append([map_size - 100, 100])

x, y = [], []
for waypoint in waypoints_path:
    x.append(-waypoint[0])
    y.append(-waypoint[1])
plt.scatter(x, y)
plt.xlim(0, -4000)
plt.ylim(-4000, 0)
plt.show()
