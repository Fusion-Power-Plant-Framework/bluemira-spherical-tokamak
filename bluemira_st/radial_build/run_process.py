from bluemira.base.parameter_frame import ParameterFrame
from bluemira.codes import systems_code_solver

from bluemira_st.params import BluemiraSTParams


def radial_build(params: BluemiraSTParams, build_config: dict) -> ParameterFrame:
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
        "tf_wp_width": {"recv": True, "send": False},
        "tf_wp_depth": {"recv": True, "send": False},
    })
    new_params = solver.execute(run_mode)

    if plot:
        solver.plot_radial_build(show=True)

    params.update_from_frame(new_params)
    params._set_param("tf_cl_ib_x", new_params.r_tf_in_centre)  # noqa: SLF001
    params._set_param("tf_cl_ob_x", new_params.r_tf_out_centre)  # noqa: SLF001
    return params
