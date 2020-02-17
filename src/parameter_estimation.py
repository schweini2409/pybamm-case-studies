#
# Parameter fitting
# Requires package 'DFO-LS'
#
import casadi  # noqa: F401
import dfols
import pybamm
import numpy as np
import matplotlib.pyplot as plt

# pybamm.set_logging_level("INFO")
model = pybamm.lithium_ion.DFN()

# create geometry
geometry = model.default_geometry

# load parameter values and process model and geometry
param = model.default_parameter_values


def electrolyte_conductivity(c_e, T, T_inf, E_k_e, R_g):
    return pybamm.InputParameter("Conductivity")


param.update(
    {
        "Cation transference number": "[input]",
        "Electrolyte conductivity [S.m-1]": electrolyte_conductivity,
    }
)
param.process_model(model)
param.process_geometry(geometry)

# set mesh
var = pybamm.standard_spatial_vars
var_pts = {var.x_n: 20, var.x_s: 20, var.x_p: 20, var.r_n: 10, var.r_p: 10}
mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)

# solve model
t_eval = np.linspace(0, 0.15, 100)
solver = pybamm.CasadiSolver(mode="fast")
solver.rtol = 1e-3
solver.atol = 1e-6


def objective(solution):
    return solution["Terminal voltage [V]"].entries


# Generate synthetic data, with noise
true_solution = solver.solve(
    model, t_eval, inputs={"Cation transference number": 0.4, "Conductivity": 0.3}
)
data = objective(true_solution)
# add random normal noise
data_plus_noise = data + 0.01 * np.random.normal(size=data.shape[0]) / np.max(data)


def prediction_error(x):
    # Hack to enforce bounds
    if np.any(x < 0):
        return 1e5 * np.ones_like(data_plus_noise)
    try:
        solution = solver.solve(
            model,
            t_eval,
            inputs={"Cation transference number": x[0], "Conductivity": x[1]},
        )
    except pybamm.SolverError:
        return 1e5 * np.ones_like(data_plus_noise)
    prediction = objective(solution)
    # Crude way of making sure we always get an answer
    if len(prediction) != len(data_plus_noise):
        return 1e5 * np.ones_like(data_plus_noise)
    else:
        out = prediction - data_plus_noise
        print(x, np.linalg.norm(out))
        return out


# Do parameter fitting to find solution (using derivative-free library)
x0 = np.array([0.7, 0.5])
soln = dfols.solve(prediction_error, x0)  # , bounds=(np.array([0]), None))
found_solution = solver.solve(
    model,
    t_eval,
    inputs={"Cation transference number": soln.x[0], "Conductivity": soln.x[1]},
)

# Generate initial guess, for plotting
init_solution = solver.solve(
    model, t_eval, inputs={"Cation transference number": x0[0], "Conductivity": x0[1]}
)

# Plot
plt.plot(true_solution["Time [h]"].entries, data_plus_noise, label="data")
plt.plot(
    found_solution["Time [h]"].entries,
    found_solution["Terminal voltage [V]"].entries,
    label="fit",
)
plt.plot(
    init_solution["Time [h]"].entries,
    init_solution["Terminal voltage [V]"].entries,
    label="initial guess",
)
plt.legend()
plt.show()
