import bpy
import numpy as np
from scipy.optimize import minimize


def C1(t):
    """ Parametric curve 1: Example - Helix """
    return np.array([t, np.sin(t), np.cos(t)])

def C2(s):
    """ Parametric curve 2: Example - Cylinder spiral """
    return np.array([np.cos(s), np.sin(s), s])

def distance_squared(params):
    """ Function to minimize: Squared Euclidean distance between C1(t) and C2(s) """
    t, s = params
    return np.sum((C1(t) - C2(s))**2)

if __name__ == "<run_path>":
    # Initial guess for (t, s)
    t_init, s_init = 0.5, np.pi / 4

    print(f"minimize(distance_squared, x0=[t_init, s_init], bounds=[(0, 10), (0, 10)]")
    # Minimize distance_squared with constraints on t and s
    result = minimize(distance_squared, x0=[t_init, s_init], bounds=[(0, 10), (0, 10)])

    print(f"result.x")
    # Extract results
    t_min, s_min = result.x
    min_dist = np.sqrt(result.fun)

    print(f"Closest parameters: t = {t_min:.6f}, s = {s_min:.6f}")
    print(f"Minimum distance: {min_dist:.6f}")