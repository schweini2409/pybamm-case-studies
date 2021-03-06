#
# Parameter fitting
# Requires package 'DFO-LS'
#
import casadi  # noqa: F401
import dfols
import pybamm
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

# pybamm.set_logging_level("INFO")
model = pybamm.lithium_ion.DFN()

# create geometry
geometry = model.default_geometry

# load parameter values and process model and geometry
param = model.default_parameter_values

param.update(
    {
        "Cation transference number": "[input]",
        "Electrolyte conductivity [S.m-1]": "[input]",
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
t_eval = np.linspace(0, 3300, 100)
solver = pybamm.CasadiSolver(mode="fast")
solver.rtol = 1e-3
solver.atol = 1e-6


def objective(solution):
    return solution["Terminal voltage [V]"].entries


# Generate synthetic data, with noise
true_solution = solver.solve(
    model,
    t_eval,
    inputs={"Cation transference number": 0.4, "Electrolyte conductivity [S.m-1]": 0.3},
)
data = objective(true_solution)
# add random normal noise
np.random.seed(42)
data_plus_noise = data + 0.01 * np.random.normal(size=data.shape[0]) / np.max(data)


def prediction_error(x):
    # Hack to enforce bounds
    if np.any(x < 0):
        return 1e5 * np.ones_like(data_plus_noise)
    try:
        solution = solver.solve(
            model,
            t_eval,
            inputs={
                "Cation transference number": x[0],
                "Electrolyte conductivity [S.m-1]": x[1],
            },
        )
    except pybamm.SolverError:
        return 1e5 * np.ones_like(data_plus_noise)
    prediction = objective(solution)
    # Crude way of making sure we always get an answer
    if len(prediction) != len(data_plus_noise):
        return 1e5 * np.ones_like(data_plus_noise)
    else:
        out = prediction - data_plus_noise
        # print(x, np.linalg.norm(out))
        return out


# Do parameter fitting to find solution (using derivative-free library)
x0 = np.array([0.7, 0.5])

soln_lsq = least_squares(prediction_error, x0, verbose=2)
soln_dfols = dfols.solve(prediction_error, x0)  # , bounds=(np.array([0]), None))

for algorithm, soln in [("scipy.least_squares", soln_lsq), ("DFO-LS", soln_dfols)]:
    print(algorithm)
    print("-" * 20)
    print(soln)
    print("-" * 20)
    found_solution = solver.solve(
        model,
        t_eval,
        inputs={
            "Cation transference number": soln.x[0],
            "Electrolyte conductivity [S.m-1]": soln.x[1],
        },
    )
    plt.plot(
        found_solution["Time [h]"].entries,
        found_solution["Terminal voltage [V]"].entries,
        label=algorithm,
    )

# Generate initial guess, for plotting
init_solution = solver.solve(
    model,
    t_eval,
    inputs={
        "Cation transference number": x0[0],
        "Electrolyte conductivity [S.m-1]": x0[1],
    },
)

# Plot
plt.plot(true_solution["Time [h]"].entries, data_plus_noise, label="data")
plt.plot(
    init_solution["Time [h]"].entries,
    init_solution["Terminal voltage [V]"].entries,
    label="initial guess",
)
plt.legend()
plt.show()
