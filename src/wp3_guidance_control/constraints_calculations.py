import numpy as np

g = 9.81   # m/s^2
h_com = 0.31    # m (COM height)

# natural frequency of inverted pendulum
omega_n = np.sqrt(g/h_com)

# natural period
T_n = 2*np.pi / omega_n

# natural frequency 
f_n = 1 / T_n 
print(f_n)