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
    R_0: Parameter[float]

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
