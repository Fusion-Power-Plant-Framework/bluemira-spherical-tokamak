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
    # the params we are interested in obtained from PROCESS
    # they must be defined bluemira side
    # in order to be read
    solver.modify_mappings({
        "n_TF": {"recv": True, "send": False},
        "R_0": {"recv": True, "send": False},
        "A": {"recv": True, "send": False},
        "I_p": {"recv": True, "send": False},
        "l_i": {"recv": True, "send": False},
        "B_0": {"recv": True, "send": False},
        "beta_p": {"recv": True, "send": False},
        "delta": {"recv": True, "send": False},
        "delta_95": {"recv": True, "send": False},
        "kappa": {"recv": True, "send": False},
        "kappa_95": {"recv": True, "send": False},
        "q_95": {"recv": True, "send": False},
    })
    new_params = solver.execute(run_mode)

    if plot:
        plot_radial_build(solver.run_directory)

    params.update_from_frame(new_params)
    return params
