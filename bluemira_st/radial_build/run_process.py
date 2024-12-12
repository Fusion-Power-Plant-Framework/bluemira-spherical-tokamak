from bluemira.base.parameter_frame import ParameterFrame
from bluemira.codes import plot_radial_build, systems_code_solver


def radial_build(params: ParameterFrame, build_config: dict) -> ParameterFrame:
    run_mode = build_config.get("run_mode", "mock")
    plot = build_config.get("plot", False)

    solver = systems_code_solver(
        params,
        {
            "run_dir": build_config["run_dir"],
            "read_dir": build_config["read_dir"],
            "template_in_dat": build_config["input_in_dat_path"],
        },
    )
    new_params = solver.execute(run_mode)

    if plot:
        plot_radial_build(solver.read_directory)

    params.update_from_frame(new_params)
    return params
