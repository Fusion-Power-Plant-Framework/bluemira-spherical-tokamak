# SPDX-FileCopyrightText: 2021-present M. Coleman, J. Cook, F. Franza
# SPDX-FileCopyrightText: 2021-present I.A. Maione, S. McIntosh
# SPDX-FileCopyrightText: 2021-present J. Morris, D. Short
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""EUDEMO reactor build parameters."""

from dataclasses import dataclass

from bluemira.base.parameter_frame import Parameter, ParameterFrame


@dataclass
class BluemiraSTParams(ParameterFrame):
    """All parameters for the Bluemira ST reactor."""

    n_TF: Parameter[int]
    n_PF: Parameter[int]

    R_0: Parameter[float]
    z_0: Parameter[float]

    # plasma parameters
    A: Parameter[float]
    I_p: Parameter[float]
    B_0: Parameter[float]
    l_i: Parameter[float]
    beta_p: Parameter[float]
    delta: Parameter[float]
    delta_95: Parameter[float]
    kappa: Parameter[float]
    kappa_95: Parameter[float]
    q_95: Parameter[float]
    shaf_shift: Parameter[float]

    # tf shape parameters
    tf_cl_ib_x: Parameter[float]
    tf_cl_ob_x: Parameter[float]

    # tf opt params
    TF_ripple_limit: Parameter[float]
    r_tf_in_centre: Parameter[float]
    r_tf_corner_inner: Parameter[float]
    r_tf_corner_outer: Parameter[float]

    # Radial build parameters
    g_cs_tf: Parameter[float]
    g_ts_tf: Parameter[float]
    g_vv_bb: Parameter[float]
    g_vv_ts: Parameter[float]
    g_pf_tf: Parameter[float]

    r_cs_in: Parameter[float]

    tf_wp_width: Parameter[float]
    tf_wp_depth: Parameter[float]
    tk_sol_ib: Parameter[float]
    tk_sol_ob: Parameter[float]
    tk_bb_ob: Parameter[float]
    tk_cs: Parameter[float]
    tk_tf_front_ib: Parameter[float]
    tk_tf_nose: Parameter[float]
    tk_tf_side: Parameter[float]
    tk_ts: Parameter[float]

    # breeder blanket parameters
    g_p_bb: Parameter[float]
    g_bb_tf_min: Parameter[float]
    tk_tf: Parameter[float]
