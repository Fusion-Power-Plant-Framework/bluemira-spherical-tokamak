# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT
"""TF Coil Designer."""

from dataclasses import dataclass

import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.look_and_feel import bluemira_debug, bluemira_print
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.builders.tf_coils import EquispacedSelector
from bluemira.equilibria.coils._grouping import CoilSet
from bluemira.geometry.parameterisations import (
    GeometryParameterisation,
    PictureFrame,
)
from bluemira.geometry.tools import make_polygon
from bluemira.geometry.wire import BluemiraWire
from bluemira.utilities.tools import get_class_from_module
from matplotlib import pyplot as plt


@dataclass
class TFCoilDesignerParams(ParameterFrame):
    """Parameters for building a TF coil."""

    # RippleConstrainedLengthGOPParams
    n_TF: Parameter[int]
    R_0: Parameter[float]
    z_0: Parameter[float]
    B_0: Parameter[float]
    TF_ripple_limit: Parameter[float]

    # WP
    tf_wp_width: Parameter[float]
    tf_wp_depth: Parameter[float]
    r_tf_in_centre: Parameter[float]
    r_tf_corner_inner: Parameter[float]
    r_tf_corner_outer: Parameter[float]
    g_pf_tf: Parameter[float]


class TFCoilDesigner(Designer[tuple[GeometryParameterisation, BluemiraWire]]):
    """TF coil shape designer."""

    params = TFCoilDesignerParams
    param_cls: type[TFCoilDesignerParams] = TFCoilDesignerParams

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict,
        coilset: CoilSet,
        lcfs_wire: BluemiraWire,
    ):
        super().__init__(params, build_config)
        self.lcfs_wire = lcfs_wire
        self.coilset = coilset

        self.file_path = self.build_config.get("file_path", None)

        if (problem_class := self.build_config.get("problem_class", None)) is not None:
            self.problem_class = get_class_from_module(problem_class)
            self.problem_settings = self.build_config.get("problem_settings", {})

            self.opt_config = self.build_config.get("optimisation_settings", {})

            self.algorithm_name = self.opt_config.get("algorithm_name", "SLSQP")
            self.opt_conditions = self.opt_config.get("conditions", {"max_eval": 100})
            self.opt_parameters = self.opt_config.get("parameters", {})

    def _get_parameterisation(self) -> PictureFrame:
        x_min = self.params.r_tf_in_centre.value
        ri = self.params.r_tf_corner_inner.value
        ro = self.params.r_tf_corner_outer.value
        offset = self.params.g_pf_tf.value
        x_max, z_min, z_max = self._get_coilset_extrema(self.coilset)
        x_max += offset
        z_min -= offset
        z_max += offset
        return PictureFrame({
            "x1": {"value": x_min, "fixed": True},
            "x2": {
                "value": x_max,
                "fixed": False,
                "lower_bound": x_max,
                "upper_bound": x_max * 1.5,
            },
            "z1": {"value": z_max, "fixed": True},
            "z2": {"value": z_min, "fixed": True},
            "ri": {"value": ri, "fixed": True},
            "ro": {"value": ro, "fixed": True},
        })

    @staticmethod
    def _get_coilset_extrema(coilset: CoilSet):
        x, z = [], []
        for coil in coilset._coils:  # noqa: SLF001
            x.extend(coil.x_boundary)
            z.extend(coil.z_boundary)
        return np.max(x), np.min(z), np.max(z)

    def _make_wp_xs(self, x_inboard) -> BluemiraWire:
        width = self.params.tf_wp_width.value / 2
        depth = self.params.tf_wp_depth.value / 2
        return make_polygon(
            {
                "x": [
                    x_inboard - width,
                    x_inboard + width,
                    x_inboard + width,
                    x_inboard - width,
                ],
                "y": [-depth, -depth, depth, depth],
                "z": 0.0,
            },
            closed=True,
        )

    def run(self) -> tuple[GeometryParameterisation, BluemiraWire]:
        """
        Run the specified design optimisation problem to generate the TF coil winding
        pack current centreline.

        Returns
        -------
        :
            The parameterisation and the winding pack cross section

        Raises
        ------
        ValueError
            No problem class specified in config or no separatrix specified
        """
        parameterisation = self._get_parameterisation()
        wp_cross_section = self._make_wp_xs(self.params.r_tf_in_centre.value)

        if not hasattr(self, "problem_class"):
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'run' mode: no problem_class"
                " specified."
            )
        if self.lcfs_wire is None:
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'run' mode: no separatrix"
                " specified"
            )

        bluemira_debug(
            "Setting up design problem with:\n"
            f"algorithm_name: {self.algorithm_name}\n"
            f"n_variables: {parameterisation.variables.n_free_variables}\n"
            f"opt_conditions: {self.opt_conditions}\n"
            f"opt_parameters: {self.opt_parameters}"
        )

        if self.problem_settings != {}:
            bluemira_debug(
                f"Applying non-default settings to problem: {self.problem_settings}"
            )
        if "ripple_selector" not in self.problem_settings:
            self.problem_settings["ripple_selector"] = EquispacedSelector(
                100, x_frac=0.5
            )
        else:
            rs_config = self.problem_settings["ripple_selector"]
            ripple_selector = get_class_from_module(
                rs_config["cls"], default_module="bluemira.builders.tf_coils"
            )
            self.problem_settings["ripple_selector"] = ripple_selector(
                **rs_config.get("args", {})
            )

        design_problem = self.problem_class(
            parameterisation,
            self.algorithm_name,
            self.opt_conditions,
            self.opt_parameters,
            self.params,
            wp_cross_section=wp_cross_section,
            ripple_wire=self.lcfs_wire,
            keep_out_zone=None,
            **self.problem_settings,
        )

        bluemira_print(f"Solving design problem: {type(design_problem).__name__}")

        result = design_problem.optimise()
        result.to_json(self.file_path)
        if self.build_config.get("plot", False):
            design_problem.plot()
            plt.show()
        return result, wp_cross_section

    def read(self) -> tuple[GeometryParameterisation, BluemiraWire]:
        """
        Read in a file to set up a specified GeometryParameterisation and extract the
        current centreline.

        Returns
        -------
        :
            The parameterisation and the winding pack cross section

        Raises
        ------
        ValueError
            file_path not specified in config
        """
        if not self.file_path:
            raise ValueError(
                f"Cannot execute {type(self).__name__} in 'read' mode: no file path"
                " specified."
            )

        parameterisation = self.parameterisation_cls.from_json(file=self.file_path)
        return (
            parameterisation,
            self._make_wp_xs(parameterisation.create_shape().bounding_box.x_min),
        )

    def mock(self) -> tuple[GeometryParameterisation, BluemiraWire]:
        """
        Mock a design of TF coils using the original parameterisation of the current
        centreline.

        Returns
        -------
        :
            The parameterisation and the winding pack cross section
        """
        parameterisation = self._get_parameterisation()
        return parameterisation, self._make_wp_xs(
            parameterisation.create_shape().bounding_box.x_min
        )
