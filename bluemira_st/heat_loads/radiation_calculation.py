import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bluemira.base.constants import raw_uc
from bluemira.equilibria import Equilibrium
from bluemira.radiation_transport.midplane_temperature_density import midplane_profiles
from bluemira.radiation_transport.radiation_profile import (
    RadiationSource,
    interpolated_field_values,
    linear_interpolator,
)
from bluemira.radiation_transport.radiation_tools import (
    FirstWallRadiationSolver,
    filtering_in_or_out,
    grid_interpolator,
    pfr_filter,
)


def radiation_profile_calculation(eq: Equilibrium, fw_shape_coords):

    fw_shape = fw_shape_coords

    # double null parameters
    sep_corrector_omp = 5e-3
    sep_corrector_imp = 6e-3
    lfs_p_fraction = 0.9
    tungsten_fraction = 1e-5

    params = {
        "sep_corrector_omp": {"value": sep_corrector_omp, "unit": "m"},
        "sep_corrector_imp": {"value": sep_corrector_imp, "unit": "m"},
        "alpha_n": {"value": 1.15, "unit": "dimensionless"},
        "alpha_t": {"value": 1.905, "unit": "dimensionless"},
        "det_t": {"value": 0.0015, "unit": "keV"},
        "eps_cool": {"value": 25.0, "unit": "eV"},
        "f_ion_t": {"value": 0.01, "unit": "keV"},
        "main_ext": {"value": None, "unit": "m"},
        "rec_ext_out_leg": {"value": 2, "unit": "m"},
        "rec_ext_in_leg": {"value": 0.2, "unit": "m"},
        "fw_lambda_q_near_omp": {"value": 0.002, "unit": "m"},
        "fw_lambda_q_far_omp": {"value": 0.1, "unit": "m"},
        "fw_lambda_q_near_imp": {"value": 0.002, "unit": "m"},
        "fw_lambda_q_far_imp": {"value": 0.1, "unit": "m"},
        "lambda_t_factor": {"value": 7, "unit": "dimensionless"},
        "lambda_n_factor": {"value": 1 / 7, "unit": "dimensionless"},
        "gamma_sheath": {"value": 7.0, "unit": "dimensionless"},
        "k_0": {"value": 2000.0, "unit": "dimensionless"},
        "lfs_p_fraction": {"value": lfs_p_fraction, "unit": "dimensionless"},
        "n_e_0": {"value": 21.93e19, "unit": "1/m^3"},
        "n_e_ped": {"value": 8.117e19, "unit": "1/m^3"},
        "n_e_sep": {"value": 1.623e19, "unit": "1/m^3"},
        "P_sep": {"value": 150, "unit": "MW"},
        "rho_ped_n": {"value": 0.94, "unit": "dimensionless"},
        "rho_ped_t": {"value": 0.976, "unit": "dimensionless"},
        "n_points_core_95": {"value": 30, "unit": "dimensionless"},
        "n_points_core_99": {"value": 15, "unit": "dimensionless"},
        "n_points_mantle": {"value": 10, "unit": "dimensionless"},
        "t_beta": {"value": 2.0, "unit": "dimensionless"},
        "T_e_0": {"value": 21.442, "unit": "keV"},
        "T_e_ped": {"value": 5.059, "unit": "keV"},
        "T_e_sep": {"value": 0.16, "unit": "keV"},
    }

    # %%
    config = {
        "f_imp_core": {"H": 1e-1, "He": 1e-2, "Xe": 1e-4, "W": tungsten_fraction},
        "f_imp_sol": {"H": 0, "He": 0, "Ar": 0.003, "Xe": 0, "W": 0},
        "tau_core": np.inf,
        "tau_sol": 10,
    }

    profiles = midplane_profiles(params=params)
    source = RadiationSource(
        eq=eq,
        firstwall_shape=fw_shape,
        params=params,
        midplane_profiles=profiles,
        core_impurities=config["f_imp_core"],
        sol_impurities=config["f_imp_sol"],
        confinement_time_core=config["tau_core"],
        confinement_time_sol=config["tau_sol"],
        source_sol_dl=0.1,
    )

    source.analyse(firstwall_geom=fw_shape)

    source.rad_map(fw_shape)
    source.plot()
    plt.show()

    # Core and SOL source: coordinates and radiation values
    x_core = source.core_rad.x_tot
    z_core = source.core_rad.z_tot
    x_sol = source.sol_rad.x_tot
    z_sol = source.sol_rad.z_tot

    # Coversion required for CHERAB
    # Core and SOL interpolating function
    f_core = linear_interpolator(
        x_core, z_core, raw_uc(source.core_rad.rad_tot, "MW", "W")
    )
    f_sol = linear_interpolator(x_sol, z_sol, raw_uc(source.sol_rad.rad_tot, "MW", "W"))

    # SOL radiation grid
    x_sol = np.linspace(min(fw_shape.x), max(fw_shape.x), 1000)
    z_sol = np.linspace(min(fw_shape.z), max(fw_shape.z), 1500)
    rad_sol_grid = interpolated_field_values(x_sol, z_sol, f_sol)

    # Filter in/out zones
    wall_filter = filtering_in_or_out(fw_shape.x, fw_shape.z)
    pfr_x_down, pfr_z_down = pfr_filter(
        source.sol_rad.separatrix, source.sol_rad.points["x_point"]["z_low"]
    )
    pfr_down_filter = filtering_in_or_out(pfr_x_down, pfr_z_down, include_points=False)

    pfr_x_up, pfr_z_up = pfr_filter(
        source.sol_rad.separatrix, source.sol_rad.points["x_point"]["z_up"]
    )
    pfr_up_filter = filtering_in_or_out(pfr_x_up, pfr_z_up, include_points=False)

    # Fetch lcfs
    lcfs = source.lcfs
    core_filter_in = filtering_in_or_out(lcfs.x, lcfs.z)
    core_filter_out = filtering_in_or_out(lcfs.x, lcfs.z, include_points=False)
    for i in range(len(x_sol)):
        for j in range(len(z_sol)):
            point = x_sol[i], z_sol[j]
            if core_filter_in(point):
                rad_sol_grid[j, i] = interpolated_field_values(
                    x_sol[i], z_sol[j], f_core
                ).item()
            else:
                rad_sol_grid[j, i] = (
                    rad_sol_grid[j, i]
                    * (wall_filter(point) * 1.0)
                    * (pfr_down_filter(point) * 1.0)
                    * (pfr_up_filter(point) * 1.0)
                    * (core_filter_out(point) * 1.0)
                ).item()

    func = grid_interpolator(x_sol, z_sol, rad_sol_grid)
    # Calculate radiation of FW points
    solver = FirstWallRadiationSolver(source_func=func, firstwall_shape=fw_shape)

    return solver.solve(verbose=True)


def export_radiation_loads_to_csv(radiation_result):

    df = pd.DataFrame({
        "detector": radiation_result.detector_numbers,
        "distance_m": radiation_result.distance,
        "power_density_W_m2": radiation_result.power_density,
        "power_density_stdev_W_m2": radiation_result.power_density_stdev,
        "detected_power_W": radiation_result.detected_power,
        "detected_power_stdev_W": radiation_result.detected_power_stdev,
        "detector_area_m2": radiation_result.detector_area,
    })

    df.to_csv("first_wall_radiation_loads.csv", index=False)
