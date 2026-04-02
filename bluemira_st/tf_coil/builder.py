# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT
"""TF Coil Builder."""

from copy import deepcopy
from dataclasses import dataclass

from bluemira.base.builder import Builder
from bluemira.base.components import Component, PhysicalComponent
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.geometry.face import BluemiraFace
from bluemira.geometry.tools import (
    offset_wire,
    sweep_shape,
)
from bluemira.geometry.wire import BluemiraWire


@dataclass
class TFCoilBuilderParams(ParameterFrame):
    """Parameters for building a TF coil."""

    tf_wp_width: Parameter[float]
    tf_wp_depth: Parameter[float]


class TFCoilBuilder(Builder):
    """Build a 3D model of a TF Coil from a given centre line."""

    params: TFCoilBuilderParams
    param_cls: type[TFCoilBuilderParams] = TFCoilBuilderParams

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict,
        tf_cl_wire: BluemiraWire,
        tf_wp_xs_wire: BluemiraWire,
    ):
        super().__init__(params, build_config)
        self.cl_wire = tf_cl_wire
        self.tf_wp_xs_wire = tf_wp_xs_wire

    def build(self) -> Component:
        """Run the full build for the TF coils."""
        return self.component_tree(
            xz=[self.build_xz()],
            xy=[Component("")],
            xyz=[self.build_xyz()],
        )

    def build_xz(self) -> PhysicalComponent:
        """Build the xz Component of the TF coils."""
        inner = offset_wire(
            self.cl_wire,
            -0.5 * self.params.tf_wp_width.value,
        )
        outer = offset_wire(
            self.cl_wire,
            0.5 * self.params.tf_wp_width.value,
        )
        return PhysicalComponent("Winding pack", BluemiraFace([outer, inner]))

    def build_xyz(self) -> PhysicalComponent:
        """Build the xyz Component of the TF coils."""
        wp_xs = deepcopy(self.tf_wp_xs_wire)
        volume = sweep_shape(wp_xs, self.cl_wire)
        return PhysicalComponent("Winding pack", volume)
