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
    # the params we are interested in obtaining from PROCESS
    # they must be defined bluemira side
    # in order to be read
    solver.modify_mappings({
        # OUT mappings changed to in/out mappings
        "R_0": {"recv": True, "send": True},
        "B_0": {"recv": True, "send": True},
        "kappa": {"recv": True, "send": True},

        # OUT mappings, restating defaults
        "I_p": {"recv": True, "send": False},
        "beta_p": {"recv": True, "send": False},
        "delta_95": {"recv": True, "send": False},
        "kappa_95": {"recv": True, "send": False},
        "tf_wp_width": {"recv": True, "send": False},
        "tf_wp_depth": {"recv": True, "send": False},
        "tk_tf_side": {"recv": True, "send": False},
        "tk_tf_front_ib": {"recv": True, "send": False},
        # NONE mappings, changed to in/out mappings
        "l_i": {"recv": True, "send": True},
        "q_95": {"recv": True, "send": True},
        # radial build specific mappings
        "r_cs_in": {"recv": True, "send": False}, # dr_bore
        "tk_cs": {"recv": True, "send": False}, # dr_cs
        "tk_tf_inboard": {"recv": True, "send": False}, # dr_tf_inboard
        "g_ts_tf": {"recv": True, "send": False}, # dr_tf_shld_gap
        "tk_ts": {"recv": True, "send": False}, # dr_shld_thermal_inboard
        "g_vv_ts": {"recv": True, "send": False}, #r_shld_vv_gap_inboard
        "tk_vv_in": {"recv": True, "send": False}, # dr_vv_inboard
        "tk_sh_in": {"recv": True, "send": False}, # dr_shld_inboard
    })
    new_params = solver.execute(run_mode)


    if plot:
        solver.plot_radial_build(show=True)

    params.update_from_frame(new_params)
    return params
