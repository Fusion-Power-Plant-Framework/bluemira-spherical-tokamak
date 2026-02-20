
"""Breeder Blanket (BB) Builder."""

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
from bluemira.display.palettes import BLUE_PALETTE
from bluemira.builders.tools import apply_component_display_options
from bluemira.geometry.wire import BluemiraWire
from bluemira.geometry.tools import (
    distance_to,
    interpolate_bspline,
    make_polygon,
    offset_wire,
    revolve_shape,
    sweep_shape,
)



@dataclass
class BBBuilderParams(ParameterFrame):
    """Parameters for building a PF coil"""
    # gaps
    g_p_bb: Parameter[float]
    g_bb_tf_min: Parameter[float]
    # thicknesses
    tk_bb: Parameter[float]
    n_TF: Parameter[int]


class BBBuilder(Builder):
    """Builder for the breeder blanket."""

    BB = "BB"

    param_cls: type[BBBuilderParams] = BBBuilderParams
    params: BBBuilderParams

    def __init__(
        self,
        params: BBBuilderParams,
        lcfs_wire: BluemiraWire,
        material_name: str,
    ):
        super().__init__(params, {"material": {self.BB: material_name}})
        self.lcfs_wire = lcfs_wire

    def build(self) -> Component:
        """Build the breeder blanket component."""
        inner_bb = offset_wire(self.lcfs_wire, self.params.g_p_bb.value, ndiscr=100)
        inner_bb = interpolate_bspline(inner_bb.vertexes, closed=True)
        outer_bb = offset_wire(inner_bb, self.params.tk_bb.value, ndiscr=100)
        outer_bb = interpolate_bspline(outer_bb.vertexes, closed=True)
        bb_xz = BluemiraFace([outer_bb, inner_bb])
        bb = revolve_shape(bb_xz, degree=360 / self.params.n_TF.value)
        mat = self.get_material(self.BB)
        pc_xz = PhysicalComponent(self.BB, bb_xz, mat)
        pc_xyz = PhysicalComponent(self.BB, bb, mat)
        apply_component_display_options(pc_xyz, color=BLUE_PALETTE["BB"][0])
        return self.component_tree(xz=[pc_xz], xy=[], xyz=[pc_xyz])
