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

import matplotlib.pyplot as plt
import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.equilibria import Equilibrium
from bluemira.equilibria.coils import Coil, CoilSet, SymmetricCircuit
from bluemira.equilibria.diagnostics import PicardDiagnosticOptions
from bluemira.equilibria.grid import Grid
from bluemira.equilibria.optimisation.problem import (
    CoilsetOptimisationProblem,
    UnconstrainedTikhonovCurrentGradientCOP,
)
from bluemira.equilibria.profiles import BetaIpProfile
from bluemira.equilibria.solve import DudsonConvergence, PicardIterator

import bluemira_st.equilibria.reference_values as refs
from bluemira_st.equilibria.tools import (
    build_reference_constraint_set,
    plasma_data,
)


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

    tk_bb_ob: Parameter[float]

    r_tf_in_centre: Parameter[float]


class ReferenceFreeBoundaryEquilibriumDesigner(Designer[Equilibrium]):
    """
    Solves a free boundary equilibrium parametrically.

    Some coils are positioned at sensible locations to try and get an initial
    free boundary equilibrium in order to be able to draw an initial first wall
    shape.

    Parameters
    ----------
    params:
        The parameters for the solver
    build_config:
        The config for the solver.
    """

    params: ReferenceFreeBoundaryEquilibriumDesignerParams
    param_cls: type[ReferenceFreeBoundaryEquilibriumDesignerParams] = (
        ReferenceFreeBoundaryEquilibriumDesignerParams
    )

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict | None = None,
    ):
        super().__init__(params, build_config)
        self.file_path: str = self.build_config.get("file_path", None)

        if self.run_mode == "read" and self.file_path is None:
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'read' mode: "
                "'file_path' missing from build config."
            )

    def _make_reference_coilset(self) -> CoilSet:
        defaults = {
            "coil_discretisation": 0.1,
        }
        coilset_config = {**defaults, **self.build_config.get("coilset", {})}

        # number of PF coils
        n_PF = self.params.n_PF.value  # noqa: N806

        if n_PF % 2 != 0:
            raise ValueError(
                "Number of PF coils must be even as the equilibrium must be symmetric."
            ) from None

        # major radius
        R_0 = self.params.R_0.value  # noqa: N806
        # aspect ratio
        A = self.params.A.value  # noqa: N806
        # elongation
        kappa = self.params.kappa.value
        # triangularity
        delta = self.params.delta.value
        # Outboard blanket thickness
        tk_bb = self.params.tk_bb_ob.value
        # plasma current
        I_p = self.params.I_p.value  # noqa: N806
        # minor radius
        R_a = R_0 / A  # noqa: N806
        # shafranov shift
        shaf_shift = refs.SHAF_SHIFT * R_a
        # null coords
        R_x = R_0 - delta * R_a  # noqa: N806
        Z_x = kappa * R_a  # noqa: N806

        # reference scaling values
        rx_p1 = refs.X_P1
        rx_p2 = refs.X_P2
        rz_p1 = refs.Z_P1
        rz_p2 = refs.Z_P2
        pf_scales = np.array([
            refs.HEIGHT_PF1,
            refs.HEIGHT_PF2,
            refs.HEIGHT_PF3,
            refs.HEIGHT_PF4,
            refs.HEIGHT_PF5,
        ])
        pf_heights = pf_scales * I_p * 0.5
        pf_As = [  # noqa: N806
            refs.ASPECTRATIO_PF1,
            refs.ASPECTRATIO_PF2,
            refs.ASPECTRATIO_PF3,
            refs.ASPECTRATIO_PF4,
            refs.ASPECTRATIO_PF5,
        ]

        x_p1 = R_x + (rx_p1 * (R_a**2))
        x_p2 = x_p1 + (rx_p2 * R_a)
        x_p3 = R_0 + R_a + tk_bb
        x_p4 = x_p3
        x_p5 = x_p4 + shaf_shift
        z_p1 = Z_x + (rz_p1 * Z_x)
        z_p2 = z_p1 + (rz_p2 * Z_x)

        r_tf_in_centre = self.params.r_tf_in_centre.value

        x_c = np.array([x_p1, x_p2, x_p3, x_p4, x_p5])
        # Shift along to account for TF coils on inboard side
        x_c += r_tf_in_centre
        z_c = [z_p1, z_p2, z_p2, Z_x, Z_x * (1 / 3)]

        coils = []
        for i, (x, z, height, pf_A) in enumerate(  # noqa: N806
            zip(x_c, z_c, pf_heights, pf_As, strict=False)
        ):
            coil_u = Coil(
                x,
                z,
                dx=height * (1.0 / pf_A),
                dz=height,
                current=0,
                ctype="PF",
                name=f"PF_u{i + 1}",
                j_max=100.0e6,
            )
            coil_l = Coil(
                x,
                -z,
                dx=height * (1.0 / pf_A),
                dz=height,
                current=0,
                ctype="PF",
                name=f"PF_l{i + 1}",
                j_max=100.0e6,
            )
            coil = SymmetricCircuit(coil_u, coil_l)
            coil.discretisation = coilset_config["coil_discretisation"]
            coils.append(coil)

        # CS reference values
        ref_h_cs = refs.HEIGHT_CS
        ref_A_cs = refs.ASPECTRATIO_CS  # noqa: N806
        ref_x_cs_u = refs.X_CS_NULL_R0

        # CS coil dimensions
        cs_height = ref_h_cs * Z_x * 0.5
        cs_width = cs_height / ref_A_cs
        # z and x coords for the CS coils near the null
        x_cs_u = ref_x_cs_u * R_0
        z_cs_u = Z_x + 0.5 * cs_height

        x_cs_0 = x_cs_u * 0.8
        z_cs_0 = cs_height

        z_cs = [
            z_cs_u,
            z_cs_u - refs.CS_SEP * cs_height * 2.0,
            z_cs_0 + (4.0 * cs_height),
            z_cs_0 + (2.0 * cs_height),
            z_cs_0,
        ]
        x_cs = np.array([x_cs_u, x_cs_u, x_cs_0, x_cs_0, x_cs_0])
        # Shift along to account for TF coils on inboard side
        x_cs += r_tf_in_centre

        for i, (x, z) in enumerate(zip(x_cs, z_cs, strict=False)):
            coil_u = Coil(
                x,
                z,
                dx=cs_width,
                dz=cs_height,
                current=0,
                ctype="CS",
                name=f"CS_u{i + 1}",
                j_max=100.0e6,
            )
            coil_l = Coil(
                x,
                -z,
                dx=cs_width,
                dz=cs_height,
                current=0,
                ctype="CS",
                name=f"CS_l{i + 1}",
                j_max=100.0e6,
            )
            coil = SymmetricCircuit(coil_u, coil_l)
            coil.discretisation = coilset_config["coil_discretisation"]
            coils.append(coil)

        return CoilSet(*coils)

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
            "nz": 129,
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
        self,
        eq: Equilibrium,
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

        eq_targets = build_reference_constraint_set(self.params)
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
        coilset: CoilSet,
        fbe_opt_problem,
    ):
        _, ax = plt.subplots()
        fbe_opt_problem.targets.plot(ax=ax)
        coilset.plot(ax=ax, label=True)
        plt.show()

    def run(self) -> Equilibrium:
        """
        Run the FreeBoundaryEquilibriumFromFixedDesigner.

        Returns
        -------
        :
            The optimised equilibrium
        """
        self.profiles = BetaIpProfile(
            self.params.beta_p.value,
            self.params.I_p.value,
            R_0=self.params.R_0.value,
            B_0=self.params.B_0.value,
        )

        ref_coilset = self._make_reference_coilset()
        eq_grid = self._make_grid()

        eq = Equilibrium(
            ref_coilset, grid=eq_grid, profiles=self.profiles, force_symmetry=True
        )

        fbe_opt_problem = self._make_fix_to_free_opt_problem(eq)

        if self.build_config.get("plot_setup", False):
            self.plot_opt_setup(
                ref_coilset,
                fbe_opt_problem,
            )

        iterator_program = self._make_iterative_solver(eq, fbe_opt_problem)
        _result = iterator_program()

        if self.build_config.get("plot", False):
            _, ax = plt.subplots()
            eq.plot(ax=ax)
            eq.coilset.plot(ax=ax, label=True)
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
        eq = Equilibrium.from_eqdsk(
            self.file_path, qpsi_positive=False, from_cocos=3, force_symmetry=True
        )
        self._update_params_from_eq(eq)
        return eq

    def _update_params_from_eq(self, eq: Equilibrium):
        self.params.update_values(plasma_data(eq), source=type(self).__name__)
