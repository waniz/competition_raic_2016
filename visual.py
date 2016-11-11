import matplotlib.pyplot as plt

plt.style.use('ggplot')


plt.xlim(0, -4000)
plt.ylim(-4000, 0)

x = [-1370, -50, -350, -2312, -400, -1929, -902]
y = [-3650, -2693, -1656, -3950, -3600, -2400, -2768]

plt.scatter(x, y)
plt.show()
