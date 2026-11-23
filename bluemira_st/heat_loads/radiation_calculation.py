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


def radiation_profile_calculation(
    eq: Equilibrium,
    fw_shape_coords,
    params: dict,
    config: dict,
):
    show_plot = False
    fw_shape = fw_shape_coords
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
    if show_plot is True:
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

    return solver.solve(verbose=False, plot=show_plot)


def export_radiation_loads_to_csv(
    radiation_result, filename="radiation_load_results.csv"
):

    df = pd.DataFrame({
        "detector": radiation_result.detector_numbers,
        "distance_m": radiation_result.distance,
        "power_density_W_m2": radiation_result.power_density,
        "power_density_stdev_W_m2": radiation_result.power_density_stdev,
        "detected_power_W": radiation_result.detected_power,
        "detected_power_stdev_W": radiation_result.detected_power_stdev,
        "detector_area_m2": radiation_result.detector_area,
    })

    df.to_csv(filename, index=False)
