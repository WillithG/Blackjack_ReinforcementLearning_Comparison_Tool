import sqlite3 as sq3
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

"""
import matplotlib.pyplot as plt

# pass data as 2d array [ [x1, y1], [x2, y2] ]
def plot_data(data):
    x_vals = [d[0] for d in data]
    y_vals = [d[1] for d in data]
    plt.plot(x_vals, y_vals)

data = []
for x in range(100):
    to_append = [x, 0]
    y_val = x ** 2
    if x % 2 == 0:
        y_val = x**3
    to_append[1] = y_val
    data.append(to_append)

plot_data(data)
plt.show()
"""

def three_d_tests():
    def get_test_data(delta=0.05):
        from matplotlib.mlab import bivariate_normal
        x = y = np.arange(-3.0, 3.0, delta)
        X, Y = np.meshgrid(x, y)

        Z1 = bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
        Z2 = bivariate_normal(X, Y, 1.5, 0.5, 1, 1)
        Z = Z2 - Z1

        X = X * 10
        Y = Y * 10
        Z = Z * 500
        return X, Y, Z

    fig = plt.figure()
    #ax = fig.add_subplot(111, projection="3d")
    x = [x for x in range(100)]
    y = [y**2 for y in range(100)]
    z = [z**3 for z in range(100)]

    x1, y1, z1 = get_test_data()

    x2 = np.array([2,1,3])
    y2 = np.array([1,2,3])

    x3 = np.array([1,2,3])
    y3 = np.array([1,2,3])

    #ax.plot_wireframe(x1, y1, z1, rstride=10, cstride=10)

    plt.plot(x2, y2)
    plt.plot(x3, y3)
    plt.show()

three_d_tests()