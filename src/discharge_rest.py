#
# Simulate discharge followed by rest
#
import pybamm
import numpy as np
import matplotlib.pyplot as plt

# load model
pybamm.set_logging_level("INFO")
model = pybamm.lithium_ion.SPMe()

# create geometry
geometry = model.default_geometry

# load parameter values and process model and geometry
param = model.default_parameter_values
param["Current function [A]"] = "[input]"
param.process_model(model)
param.process_geometry(geometry)

# set mesh
mesh = pybamm.Mesh(geometry, model.default_submesh_types, model.default_var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)

# solve model during discharge stage (1 hour)
t_end = 3600
t_eval1 = np.linspace(0, t_end, 120)
solution1 = model.default_solver.solve(
    model, t_eval1, inputs={"Current function [A]": 1}
)

# process variables for later plotting
time1 = solution1["Time [h]"]
voltage1 = solution1["Terminal voltage [V]"]
current1 = solution1["Current [A]"]

# solve again with zero current, using last step of solution1 as initial conditions
# Note: need to update model.concatenated_initial_conditions *after* update_model,
# as update_model updates model.concatenated_initial_conditions, by concatenting
# the (unmodified) initial conditions for each variable
model.concatenated_initial_conditions = pybamm.Vector(solution1.y[:, -1][:, np.newaxis])

# simulate 1 hour of rest
t_start = solution1["Time [s]"].entries[-1]
t_end = t_start + 3600
t_eval2 = np.linspace(t_start, t_end, 120)
solution2 = model.default_solver.solve(
    model, t_eval2, inputs={"Current function [A]": 0}
)

# process variables for later plotting
time2 = solution2["Time [h]"]
voltage2 = solution2["Terminal voltage [V]"]
current2 = solution2["Current [A]"]

# plot
plt.subplot(121)
plt.plot(time1.entries, voltage1.entries, time2.entries, voltage2.entries)
plt.xlabel("Time [h]")
plt.ylabel("Voltage [V]")
plt.subplot(122)
plt.plot(time1.entries, current1.entries, time2.entries, current2.entries)
plt.xlabel("Time [h]")
plt.ylabel("Current [A]")

plt.tight_layout()
plt.show()
