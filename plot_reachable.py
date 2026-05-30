import numpy as np
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

def plot_jump_reach(v_x, v_jump, v_max, g, t_y_max, t_max):
    dx_max = v_x * (t_max + 2)
    dx = np.linspace(0, dx_max, 2000)

    t1 = dx / v_x

    maximum_y = v_jump * t_y_max - (g * t_y_max**2) / 2

    # Region 1: ascending
    t0 = np.linspace(0, t_y_max, 200)
    x0 = t0 * v_x
    y0 = np.ones_like(t0) * maximum_y

    # Region 2: parabolic fall

    t1 = np.linspace(t_y_max, t_max, 200)
    t01 = np.concatenate([t0, t1])
    x01 = t01 * v_x
    y1= v_jump * t01 - (g * t01**2) / 2

    # Region 3: linear fall
    t2 = np.linspace(t_max, t_max + 5, 200)
    x2 = t2 * v_x
    y2 =  (v_jump * t_max - (g * t_max**2) / 2 - v_max * (t2 - t_max)
    )

    
    print(t_y_max, t_max)
    plt.figure(figsize=(10, 6))

    plt.plot(x0, y0, color='blue', label=r"t $\leq t_{max}$", lw=3)
    plt.fill_between(x0, y0, y1[:len(x0)], color='blue', alpha=0.3)
    plt.plot(x01, y1, color='orange', label=r"$v_{y} < v_{y,max}$", lw=3)
    plt.fill_between(x01, y1, 0, color='orange', alpha=0.3)
    plt.plot(x2, y2, color='red', lw=3, label=r'$v_{y} \geq v_{y,max}$')
    plt.fill_between(x2, y2, 0, color='red', alpha=0.3)

    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlabel("dx", fontsize=20)
    plt.ylabel("y_max", fontsize=20)
    plt.grid(True)
    plt.legend(loc='upper right', fontsize=15)
    plt.savefig("reachable.png")
    print("saved")


if __name__ == "__main__":


    plot_jump_reach(v_x=10, v_jump=10, v_max=5, g=0.9, t_y_max=10/0.9, t_max=(15/0.9))