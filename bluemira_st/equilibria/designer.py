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

    tk_bb: Parameter[float]

    # tf shape parameters
    tf_wp_width: Parameter[float]
    tf_pf_gap: Parameter[float]


class ReferenceFreeBoundaryEquilibriumDesigner(Designer[Equilibrium]):
    """
    Solves a free boundary equilibrium from .

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
        # blanket thickness
        tk_bb = self.params.tk_bb.value
        # Plasma current
        I_p = self.params.I_p.value  # noqa: N806

        # minor radius
        R_a = R_0 / A  # noqa: N806
        # Shafranov shift,
        shaf_shift = refs.REF_SHAF_SHIFT * R_a

        # Null coords
        R_x = R_0 - delta * R_a  # noqa: N806
        Z_x = kappa * R_a  # noqa: N806

        # Reference scaling values, put into separate file
        rx_p1 = refs.REF_X_P1
        rz_p1 = refs.REF_Z_P1
        rz_p2 = refs.REF_Z_P2
        # rX_p3 = refs.REF_X_P3

        z_p1 = Z_x + (rz_p1 * Z_x)
        z_p2 = z_p1 + (rz_p2 * Z_x)
        x_p1 = R_x + (rx_p1 * R_a)
        x_p3 = R_0 + refs.REF_X_P3_RAW
        x_p4 = R_0 + tk_bb + R_a  # + shaf_shift
        x_p5 = x_p4 + shaf_shift  # R_0 + R_a + tk_bb

        x_c = [x_p1, R_0, x_p3, x_p4, x_p5]
        z_c = [z_p1, z_p2, z_p2, Z_x, Z_x * (1 / 3)]

        pf_scale = I_p * refs.REF_HEIGHT_PF
        pf_A = 1.0 / refs.REF_ASPECTRATIO_PF  # noqa: N806

        coils = []
        for i, (x, z) in enumerate(zip(x_c, z_c, strict=False)):
            coil_u = Coil(
                x,
                z,
                dx=pf_scale * pf_A,
                dz=pf_scale,
                current=0,
                ctype="PF",
                name=f"PF_u{i + 1}",
                j_max=100.0e6,
            )
            coil_l = Coil(
                x,
                -z,
                dx=pf_scale * pf_A,
                dz=pf_scale,
                current=0,
                ctype="PF",
                name=f"PF_l{i + 1}",
                j_max=100.0e6,
            )
            coil = SymmetricCircuit(coil_u, coil_l)
            coil.discretisation = coilset_config["coil_discretisation"]
            coils.append(coil)

        # CS reference values
        rh_cs = refs.REF_HEIGHT_CS_QU
        rA_cs = refs.REF_ASPECTRATIO_CS  # noqa: N806
        rx_cs_u = refs.REF_X_CS_NULL
        # rz_cs1 = refs.REF_Z_CSU
        # rz_cs2 = refs.REF_Z_CSL

        cs_height = rh_cs * (Z_x**4) * 0.5
        cs_width = cs_height / rA_cs
        x_cs_u = rx_cs_u * R_a
        z_cs_0 = cs_height
        x_cs_0 = x_cs_u - 2.0 * cs_width

        z_cs = [
            Z_x + cs_height,
            Z_x - 1.5 * cs_height,
            z_cs_0 + (4.0 * cs_height),
            z_cs_0 + (2.0 * cs_height),
            z_cs_0,
        ]
        x_cs = [x_cs_u, x_cs_u, x_cs_0, x_cs_0, x_cs_0]

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
        self,
        eq: Equilibrium,
        # lcfs_coords: Coordinates
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

        # constraint_config = opt_config.get("constraint", {})

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
        # lcfs_discr_coords: Coordinates,
        coilset: CoilSet,
        fbe_opt_problem,
        # tf_cl_wire: BluemiraWire,
    ):
        _, ax = plt.subplots()
        fbe_opt_problem.targets.plot(ax=ax)
        coilset.plot(ax=ax, label=True)
        # ax.plot(lcfs_discr_coords.x, lcfs_discr_coords.z, color="black")
        # plot_2d(tf_cl_wire, ax=ax)
        plt.show()

    def run(self) -> Equilibrium:
        """
        Run the FreeBoundaryEquilibriumFromFixedDesigner.

        Returns
        -------
        :
            The optimised equilibrium
        """
        # lcfs_parameterisation = self._create_lcfs_parameterisation()
        # lcfs_wire = lcfs_parameterisation.create_shape()

        self.profiles = BetaIpProfile(
            self.params.beta_p.value,
            self.params.I_p.value,
            R_0=self.params.R_0.value,
            B_0=self.params.B_0.value,
        )

        # lcfs_discr_coords = self.lcfs_wire.discretise(byedges=True, ndiscr=200)

        ref_coilset = self._make_reference_coilset()
        eq_grid = self._make_grid()

        eq = Equilibrium(ref_coilset, grid=eq_grid, profiles=self.profiles)

        fbe_opt_problem = self._make_fix_to_free_opt_problem(eq)

        if self.build_config.get("plot_setup", False):
            self.plot_opt_setup(
                # lcfs_discr_coords,
                ref_coilset,
                fbe_opt_problem,
                # self.tf_cl_wire
            )

        iterator_program = self._make_iterative_solver(eq, fbe_opt_problem)
        _result = iterator_program()

        if self.build_config.get("plot", False):
            _, ax = plt.subplots()
            eq.plot(ax=ax)
            eq.coilset.plot(ax=ax, label=True)
            # ax.plot(lcfs_discr_coords.x, lcfs_discr_coords.z, color="black")
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
