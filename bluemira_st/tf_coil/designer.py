# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT
"""TF Coil Designer."""

from dataclasses import dataclass

import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.builders.tf_coils import EquispacedSelector, RippleConstrainedLengthGOP
from bluemira.equilibria.coils._grouping import CoilSet
from bluemira.geometry.parameterisations import (
    GeometryParameterisation,
    PictureFrame,
)
from bluemira.geometry.tools import make_polygon
from bluemira.geometry.wire import BluemiraWire


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
        self.initial_tf_cl = self._build_initial_tf_cl(coilset)
        self.lcfs_wire = lcfs_wire

    def _build_initial_tf_cl(self, coilset: CoilSet) -> PictureFrame:
        x_min = self.params.r_tf_in_centre.value
        ri = self.params.r_tf_corner_inner.value
        ro = self.params.r_tf_corner_outer.value
        offset = self.params.g_pf_tf.value
        x_max, z_min, z_max = self._get_coilset_extrema(coilset)
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

    def _build_wp_xz(self) -> BluemiraWire:
        width = self.params.tf_wp_width.value / 2
        depth = self.params.tf_wp_depth.value / 2
        return make_polygon(
            {
                "x": [-width, width, width, -width],
                "y": [-depth, -depth, depth, depth],
                "z": 0.0,
            },
            closed=True,
        )

    def _build_gop(self, wp_xs: BluemiraWire) -> RippleConstrainedLengthGOP:
        defaults = {"max_eval": 100, "ftol_rel": 1e-6, "n_ripple_pts": 10}
        opt_config = {**defaults, **self.build_config.get("optimisation", {})}
        ripple_selector_pts = opt_config.pop("n_ripple_pts")
        return RippleConstrainedLengthGOP(
            self.initial_tf_cl,
            "SLSQP",
            opt_conditions=opt_config,
            opt_parameters={},
            params=self.params,
            wp_cross_section=wp_xs,
            ripple_wire=self.lcfs_wire,
            ripple_selector=EquispacedSelector(ripple_selector_pts),
        )

    def run(self) -> tuple[GeometryParameterisation, BluemiraWire]:
        """Run the design of the TF coil."""
        wp_xs = self._build_wp_xz()
        gop = self._build_gop(wp_xs)
        result = gop.optimise()

        if self.build_config.get("plot"):
            gop.plot()

        return result, wp_xs
