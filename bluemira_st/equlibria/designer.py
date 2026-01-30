# SPDX-FileCopyrightText: 2021-present M. Coleman, J. Cook, F. Franza
# SPDX-FileCopyrightText: 2021-present I.A. Maione, S. McIntosh
# SPDX-FileCopyrightText: 2021-present J. Morris, D. Short
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Designer for an `Equilibrium` solving an unconstrained Tikhnov current
gradient coil-set optimisation problem.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.display import plot_2d
from bluemira.equilibria import Equilibrium
from bluemira.equilibria.coils import Coil, CoilSet, SymmetricCircuit
from bluemira.equilibria.diagnostics import PicardDiagnosticOptions
from bluemira.equilibria.grid import Grid
from bluemira.equilibria.optimisation.problem import (
    CoilsetOptimisationProblem,
    UnconstrainedTikhonovCurrentGradientCOP,
)
from bluemira.equilibria.profiles import BetaIpProfile, Profile
from bluemira.equilibria.shapes import ZakharovLCFS
from bluemira.equilibria.solve import DudsonConvergence, PicardIterator
from bluemira.geometry.tools import offset_wire
from bluemira.geometry.wire import BluemiraWire

from bluemira_st.equlibria.tools import (
    build_reference_constraint_set,
    get_intersections_from_angles,
    plasma_data,
)

if TYPE_CHECKING:
    from bluemira.geometry.coordinates import Coordinates


@dataclass
class DummyFixedEquilibriumDesignerParams(ParameterFrame):
    """
    Parameter frame for the dummy equilibrium designer.
    """

    R_0: Parameter[float]
    z_0: Parameter[float]
    B_0: Parameter[float]
    I_p: Parameter[float]
    l_i: Parameter[float]
    beta_p: Parameter[float]
    A: Parameter[float]
    delta: Parameter[float]
    delta_95: Parameter[float]
    kappa: Parameter[float]
    kappa_95: Parameter[float]


class DummyFixedEquilibriumDesigner(Designer[tuple[BluemiraWire, Profile]]):
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

    def _create_lcfs_parameterisation(self) -> ZakharovLCFS:
        """
        Create the values for the LCFS parameterisation.

        Returns
        -------
        :
            LCFS parameterisation
        """
        p = self.params
        # these adjust the default values of ZakharovLCFS parametrisation
        return ZakharovLCFS({
            "r_0": {
                "value": p.R_0.value,
            },
            "z_0": {
                "value": 0.0,
            },
            "a": {
                "value": p.R_0.value / p.A.value,
            },
            "kappa": {
                "value": p.kappa_95.value,
            },
            "delta": {
                "value": p.delta_95.value,
            },
        })

    def run(self) -> tuple[BluemiraWire, Profile]:
        """
        Run the DummyFixedEquilibriumDesigner.

        Returns
        -------
        lcfs_coords:
            LCFS coordinate positions
        profiles:
            Equilibria profiles
        """
        lcfs_parameterisation = self._create_lcfs_parameterisation()
        lcfs_wire = lcfs_parameterisation.create_shape()

        profiles = BetaIpProfile(
            self.params.beta_p.value,
            # self.params.l_i.value,
            self.params.I_p.value,
            R_0=self.params.R_0.value,
            B_0=self.params.B_0.value,
            # li_rel_tol=self.build_config.get("li_rel_tol", 0.01),
            # li_min_iter=self.build_config.get("li_min_iter", 2),
        )
        return lcfs_wire, profiles


@dataclass
class ReferenceFreeBoundaryEquilibriumDesignerParams(ParameterFrame):
    """Parameters for running the fixed boundary equilibrium solver."""

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

    q_95: Parameter[float]
    shaf_shift: Parameter[float]

    n_PF: Parameter[int]

    # tf shape parameters
    tf_wp_width: Parameter[float]
    tf_pf_gap: Parameter[float]


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
    lcfs_wire:
        Wire of the desired LCFS shape
    profiles:
        Profile object describing the equilibrium profiles
    tf_cl_wire:
        TF coil centreline wire
    """

    params: ReferenceFreeBoundaryEquilibriumDesignerParams
    param_cls: type[ReferenceFreeBoundaryEquilibriumDesignerParams] = (
        ReferenceFreeBoundaryEquilibriumDesignerParams
    )

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict | None = None,
        lcfs_wire: BluemiraWire | None = None,
        profiles: Profile | None = None,
        tf_cl_wire: BluemiraWire | None = None,
    ):
        super().__init__(params, build_config)
        self.file_path: str = self.build_config.get("file_path", None)
        self.lcfs_wire = lcfs_wire
        self.profiles = profiles
        self.tf_cl_wire = tf_cl_wire

        if self.run_mode == "read" and self.file_path is None:
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'read' mode: "
                "'file_path' missing from build config."
            )

        if self.run_mode == "run" and (
            (self.lcfs_wire is None) or (self.profiles is None)
        ):
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'run' mode without "
                "input LCFS shape or profiles."
            )

    def _make_reference_coilset(self, lcfs_coords: Coordinates) -> CoilSet:
        defaults = {
            "coil_discretisation": 200,
        }
        coilset_config = {**defaults, **self.build_config.get("coilset", {})}

        # total thickness of the TF coil face in the z direction
        tf_wp_width = self.params.tf_wp_width.value
        # gap between the TF coil face and the PF coils
        tf_pf_gap = self.params.tf_pf_gap.value
        # number of PF coils
        n_PF = self.params.n_PF.value  # noqa: N806

        if n_PF % 2 != 0:
            raise ValueError(
                "Number of PF coils must be even as the equilibrium must be symmetric."
            ) from None

        pf_track = offset_wire(
            self.tf_cl_wire,
            tf_wp_width + tf_pf_gap,
        )

        arg_z_max = np.argmax(lcfs_coords.z)

        r_mid = 0.5 * (np.min(lcfs_coords.x) + np.max(lcfs_coords.x))

        d_delta_u = lcfs_coords.x[arg_z_max] - r_mid
        d_kappa_u = lcfs_coords.z[arg_z_max]

        angle_upper = np.arctan2(d_kappa_u, d_delta_u)
        angles = np.linspace(angle_upper, 0, n_PF // 2 + 1)[:-1]
        x_c, z_c = get_intersections_from_angles(pf_track, r_mid, 0.0, angles)

        pf_coils = []
        for i, (x, z) in enumerate(zip(x_c, z_c, strict=False)):
            coil_u = Coil(
                x,
                z,
                current=0,
                ctype="PF",
                name=f"PF_u{i + 1}",
                j_max=100.0e6,
            )
            coil_l = Coil(
                x,
                -z,
                current=0,
                ctype="PF",
                name=f"PF_l{i + 1}",
                j_max=100.0e6,
            )
            coil = SymmetricCircuit(coil_u, coil_l)
            coil.discretisation = coilset_config["coil_discretisation"]
            pf_coils.append(coil)
        return CoilSet(*pf_coils)

    def _make_grid(self) -> Grid:
        """
        Make a finite difference Grid for an Equilibrium.

        Returns
        -------
        :
            Finite difference grid for an Equilibrium
        """
        defaults = {
            "grid_scale_x": 2.0,
            "grid_scale_z": 2.0,
            "nx": 65,
            "nz": 65,
        }
        grid_settings = {**defaults, **self.build_config.get("grid", {})}

        # major radius
        R_0 = self.params.R_0.value  # noqa: N806
        # aspect ratio
        A = self.params.A.value  # noqa: N806
        # elongation
        kappa = self.params.kappa.value

        scale_x = grid_settings["grid_scale_x"]
        scale_z = grid_settings["grid_scale_z"]
        nx = grid_settings["nx"]
        nz = grid_settings["nz"]

        x_min, x_max = R_0 - scale_x * (R_0 / A), R_0 + scale_x * (R_0 / A)
        z_min, z_max = -scale_z * (kappa * R_0 / A), scale_z * (kappa * R_0 / A)

        return Grid(x_min, x_max, z_min, z_max, nx, nz)

    def _make_fix_to_free_opt_problem(
        self, eq: Equilibrium, lcfs_coords: Coordinates
    ) -> UnconstrainedTikhonovCurrentGradientCOP:
        """
        Create the optimisation problem for the equilibrium.

        Returns
        -------
        :
            The optimisation problem
        """
        defaults = {
            "gamma": 1e-8,
        }
        opt_config = {**defaults, **self.build_config.get("optimisation", {})}

        constraint_config = opt_config.get("constraint", {})

        eq_targets = build_reference_constraint_set(constraint_config, lcfs_coords)
        return UnconstrainedTikhonovCurrentGradientCOP(
            eq, eq_targets, gamma=opt_config["gamma"]
        )

    def _make_iterative_solver(
        self, eq: Equilibrium, opt_problem: CoilsetOptimisationProblem
    ) -> PicardIterator:
        """
        Create the iterative solver for the equilibrium.

        Returns
        -------
        :
            The iterative solver
        """
        defaults = {
            "plot": False,
            "iter_err_max": 1e-6,
            "max_iter": 100,
            "relaxation": 0.02,
        }
        solver_config: dict = {**defaults, **self.build_config.get("solver", {})}

        return PicardIterator(
            eq,
            opt_problem,
            fixed_coils=True,
            convergence=DudsonConvergence(solver_config["iter_err_max"]),
            diagnostic_plotting=PicardDiagnosticOptions(plot=solver_config["plot"]),
            maxiter=solver_config["max_iter"],
            relaxation=solver_config["relaxation"],
        )

    @staticmethod
    def plot_opt_setup(
        lcfs_discr_coords: Coordinates,
        coilset: CoilSet,
        fbe_opt_problem,
        tf_cl_wire: BluemiraWire,
    ):
        _, ax = plt.subplots()
        fbe_opt_problem.targets.plot(ax=ax)
        coilset.plot(ax=ax, label=True)
        ax.plot(lcfs_discr_coords.x, lcfs_discr_coords.z, color="black")
        plot_2d(tf_cl_wire, ax=ax)
        plt.show()

    def run(self) -> Equilibrium:
        """
        Run the FreeBoundaryEquilibriumFromFixedDesigner.

        Returns
        -------
        :
            The optimised equilibrium
        """
        # 200 is arb and sufficient
        lcfs_discr_coords = self.lcfs_wire.discretise(byedges=True, ndiscr=200)

        ref_coilset = self._make_reference_coilset(lcfs_discr_coords)
        eq_grid = self._make_grid()

        eq = Equilibrium(ref_coilset, grid=eq_grid, profiles=self.profiles)

        fbe_opt_problem = self._make_fix_to_free_opt_problem(eq, lcfs_discr_coords)

        if self.build_config.get("plot_setup", False):
            self.plot_opt_setup(
                lcfs_discr_coords, ref_coilset, fbe_opt_problem, self.tf_cl_wire
            )

        iterator_program = self._make_iterative_solver(eq, fbe_opt_problem)
        _result = iterator_program()

        if self.build_config.get("plot", False):
            _, ax = plt.subplots()
            eq.plot(ax=ax)
            eq.coilset.plot(ax=ax, label=True)
            ax.plot(lcfs_discr_coords.x, lcfs_discr_coords.z, color="black")
            fbe_opt_problem.targets.plot(ax=ax)
            plt.show()

        if self.build_config.get("save", False):
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

    def _update_params_from_eq(self, eq: Equilibrium):
        self.params.update_values(plasma_data(eq), source=type(self).__name__)
