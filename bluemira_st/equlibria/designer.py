# SPDX-FileCopyrightText: 2021-present M. Coleman, J. Cook, F. Franza
# SPDX-FileCopyrightText: 2021-present I.A. Maione, S. McIntosh
# SPDX-FileCopyrightText: 2021-present J. Morris, D. Short
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Designer for an `Equilibrium` solving an unconstrained Tikhnov current
gradient coil-set optimisation problem.
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.look_and_feel import bluemira_warn
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.equilibria import Equilibrium
from bluemira.equilibria.optimisation.problem import (
    UnconstrainedTikhonovCurrentGradientCOP,
)
from bluemira.equilibria.profiles import BetaLiIpProfile, Profile
from bluemira.equilibria.solve import DudsonConvergence, PicardIterator
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.tools import make_circle, make_polygon
from bluemira.geometry.wire import BluemiraWire
from bluemira.utilities.tools import get_class_from_module
from eudemo.equilibria.tools import (
    ReferenceConstraints,
    handle_lcfs_shape_input,
)

from bluemira_st.equlibria.tools import (
    ReferenceEquilibriumParams,
    make_reference_equilibrium,
    plasma_data,
)


@dataclass
class DummyFixedEquilibriumDesignerParams(ParameterFrame):
    """
    Parameter frame for the dummy equilibrium designer.
    """

    R_0: Parameter[float]
    B_0: Parameter[float]
    I_p: Parameter[float]
    l_i: Parameter[float]
    beta_p: Parameter[float]
    A: Parameter[float]
    delta: Parameter[float]
    delta_95: Parameter[float]
    kappa: Parameter[float]
    kappa_95: Parameter[float]


class DummyFixedEquilibriumDesigner(Designer[tuple[Coordinates, Profile]]):
    """
    Dummy equilibrium designer that produces a LCFS shape and a profile
    object to be used in later reference free boundary equilibrium
    designers.
    """

    params: DummyFixedEquilibriumDesignerParams
    param_cls: type[DummyFixedEquilibriumDesignerParams] = (
        DummyFixedEquilibriumDesignerParams
    )

    def __init__(self, params, build_config):
        super().__init__(params, build_config)

    def run(self) -> tuple[Coordinates, Profile]:
        """
        Run the DummyFixedEquilibriumDesigner.

        Returns
        -------
        lcfs_coords:
            LCFS coordinate positions
        profiles:
            Equilibria profiles
        """
        param_cls = self.build_config.get(
            "param_class", "bluemira.equilibria.shapes::JohnerLCFS"
        )
        param_cls = get_class_from_module(param_cls)
        shape_config = self.build_config.get("shape_config", {})
        input_dict = handle_lcfs_shape_input(param_cls, self.params, shape_config)
        lcfs_parameterisation = param_cls(input_dict)

        default_settings = {
            "n_points": 200,
            "li_rel_tol": 0.01,
            "li_min_iter": 2,
        }
        settings = self.build_config.get("settings", {})
        settings = {**default_settings, **settings}
        lcfs_coords = lcfs_parameterisation.create_shape().discretise(
            byedges=True, ndiscr=settings["n_points"]
        )

        profiles = BetaLiIpProfile(
            self.params.beta_p.value,
            self.params.l_i.value,
            self.params.I_p.value,
            R_0=self.params.R_0.value,
            B_0=self.params.B_0.value,
            li_rel_tol=settings["li_rel_tol"],
            li_min_iter=settings["li_min_iter"],
        )
        return lcfs_coords, profiles


@dataclass
class ReferenceFreeBoundaryEquilibriumDesignerParams(ParameterFrame):
    """Parameters for running the fixed boundary equilibrium solver."""

    A: Parameter[float]
    B_0: Parameter[float]
    I_p: Parameter[float]
    kappa: Parameter[float]
    R_0: Parameter[float]

    # Updated parameters
    delta_95: Parameter[float]
    delta: Parameter[float]
    kappa_95: Parameter[float]
    q_95: Parameter[float]
    beta_p: Parameter[float]
    l_i: Parameter[float]
    shaf_shift: Parameter[float]


class ReferenceFreeBoundaryEquilibriumDesigner(Designer[Equilibrium]):
    """
    Solves a free boundary equilibrium from a LCFS shape and profiles.

    Some coils are positioned at sensible locations to try and get an initial
    free boundary equilibrium in order to be able to draw an initial first wall
    shape.

    Parameters
    ----------
    params:
        The parameters for the solver
    build_config:
        The config for the solver.
    lcfs_coords:
        Coordinates for the desired LCFS shape
    profiles:
        Profile object describing the equilibrium profiles
    """

    params: ReferenceFreeBoundaryEquilibriumDesignerParams
    param_cls: type[ReferenceFreeBoundaryEquilibriumDesignerParams] = (
        ReferenceFreeBoundaryEquilibriumDesignerParams
    )

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict | None = None,
        lcfs_coords: Coordinates | None = None,
        profiles: Profile | None = None,
    ):
        super().__init__(params, build_config)
        self.file_path: str = self.build_config.get("file_path", None)
        self.lcfs_coords = lcfs_coords
        self.profiles = profiles

        if self.run_mode == "read" and self.file_path is None:
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'read' mode: "
                "'file_path' missing from build config."
            )
        self.opt_problem = None

        if self.run_mode == "run" and (
            (self.lcfs_coords is None) or (self.profiles is None)
        ):
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'run' mode without "
                "input LCFS shape or profiles."
            )

    def run(self) -> Equilibrium:
        """
        Run the FreeBoundaryEquilibriumFromFixedDesigner.

        Returns
        -------
        :
            The optimised equilibrium
        """
        if (save := self.build_config.get("save", False)) and self.file_path is None:
            raise ValueError(
                "Cannot execute save equilibrium: 'file_path' missing from build config."
            )

        lcfs_shape = make_polygon(self.lcfs_coords, closed=True)

        defaults = {
            "relaxation": 0.02,
            "coil_discretisation": 0.3,
            "gamma": 1e-8,
            "iter_err_max": 1e-2,
            "max_iter": 30,
        }
        settings = self.build_config.get("settings", {})
        settings = {**defaults, **settings}

        eq = make_reference_equilibrium(
            ReferenceEquilibriumParams.from_frame(self.params),
            tf_coil_boundary,
            lcfs_shape,
            self.profiles,
            self.build_config.get("grid_settings", {}),
        )
        # TODO: Check coil discretisation is sensible when size not set...
        discretisation = settings.pop("coil_discretisation")
        # eq.coilset.discretisation = settings.pop("coil_discretisation")
        eq.coilset.get_coiltype("CS").discretisation = discretisation

        self.opt_problem = self._make_fbe_opt_problem(
            eq, lcfs_shape, len(self.lcfs_coords.x), settings.pop("gamma")
        )

        iter_err_max = settings.pop("iter_err_max")
        max_iter = settings.pop("max_iter")
        settings["maxiter"] = max_iter  # TODO: Standardise name in PicardIterator
        iterator_program = PicardIterator(
            eq,
            self.opt_problem,
            convergence=DudsonConvergence(iter_err_max),
            plot=self.build_config.get("plot", False),
            fixed_coils=True,
            **settings,
        )
        self._result = iterator_program()

        if self.build_config.get("plot", False):
            _, ax = plt.subplots()
            eq.plot(ax=ax)
            eq.coilset.plot(ax=ax, label=True)
            ax.plot(self.lcfs_coords.x, self.lcfs_coords.z, "", marker="o")
            self.opt_problem.targets.plot(ax=ax)
            plt.show()

        if save:
            eq.to_eqdsk(self.file_path, directory=str(Path().cwd()))

        self._update_params_from_eq(eq)

        return eq

    def read(self) -> Equilibrium:
        """Load an equilibrium from a file.

        Returns
        -------
        :
            The equilibrium read in
        """
        eq = Equilibrium.from_eqdsk(self.file_path, qpsi_positive=False, from_cocos=3)
        self._update_params_from_eq(eq)
        return eq

    def _make_tf_boundary(
        self,
        lcfs_shape: BluemiraWire,
    ) -> BluemiraWire:
        coords = lcfs_shape.discretise(byedges=True, ndiscr=200)
        xu_arg = np.argmax(coords.z)
        xl_arg = np.argmin(coords.z)
        xz_min, z_min = coords.x[xl_arg], coords.z[xl_arg]
        xz_max, z_max = coords.x[xu_arg], coords.z[xu_arg]
        x_circ = min(xz_min, xz_max)
        z_circ = z_max - abs(z_min)
        r_circ = 0.5 * (z_max + abs(z_min))

        offset_value = self.params.tk_bb_ob.value + self.params.tk_vv_out.value + 2.5
        semi_circle = make_circle(
            r_circ + offset_value,
            center=(x_circ, 0, z_circ),
            start_angle=-90,
            end_angle=90,
            axis=(0, 1, 0),
        )

        xs, zs = semi_circle.start_point().xz.T[0]
        xe, ze = semi_circle.end_point().xz.T[0]
        r_cs_out = self.params.r_cs_in.value + self.params.tk_cs.value

        lower_wire = make_polygon({"x": [r_cs_out, xs], "y": [0, 0], "z": [zs, zs]})
        upper_wire = make_polygon({"x": [xe, r_cs_out], "y": [0, 0], "z": [ze, ze]})

        return BluemiraWire([lower_wire, semi_circle, upper_wire])

    @staticmethod
    def _make_fbe_opt_problem(
        eq: Equilibrium, lcfs_shape: BluemiraWire, n_points: int, gamma: float
    ) -> UnconstrainedTikhonovCurrentGradientCOP:
        """
        Create the `UnconstrainedTikhonovCurrentGradientCOP` optimisation problem.

        Returns
        -------
        :
            Optimisation problem
        """
        eq_targets = ReferenceConstraints(lcfs_shape, n_points)
        return UnconstrainedTikhonovCurrentGradientCOP(
            eq.coilset, eq, eq_targets, gamma=gamma
        )

    def _update_params_from_eq(self, eq: Equilibrium):
        self.params.update_values(plasma_data(eq), source=type(self).__name__)
