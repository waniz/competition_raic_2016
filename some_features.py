"""
http://stackoverflow.com/questions/25342072/computing-and-drawing-vector-fields
"""

import numpy as np
import matplotlib.pyplot as plt


y, x = np.mgrid[10: -10:100j, 10: -10:100j]

x_obstacle, y_obstacle = 0.0, 0.0
alpha_obstacle, a_obstacle, b_obstacle = 1.0, 1e3, 2e3

p = -alpha_obstacle * np.exp(-((x - x_obstacle)**2 / a_obstacle + (y - y_obstacle)**2 / b_obstacle))

dy, dx = np.gradient(p, np.diff(y[:2, 0]), np.diff(x[0, :2]))

skip = (slice(None, None, 3), slice(None, None, 3))

fig, ax = plt.subplots()
im = ax.imshow(p, extent=[x.min(), x.max(), y.min(), y.max()])
ax.quiver(x[skip], y[skip], dx[skip], dy[skip])

fig.colorbar(im)
ax.set(aspect=1, title='Quiver Plot')
plt.show()
