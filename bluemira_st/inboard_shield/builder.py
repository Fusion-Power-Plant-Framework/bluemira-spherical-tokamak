
"""Inboard Shield (IS) Builder."""

from dataclasses import dataclass

import numpy as np
from bluemira.base.builder import Builder
from bluemira.base.components import Component, PhysicalComponent
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.geometry.face import BluemiraFace
from bluemira.geometry.coordinates import Coordinates
from bluemira.builders.tools import get_n_sectors

from bluemira.geometry.tools import (
    revolve_shape,
    make_polygon,
)
from bluemira.display.palettes import BLUE_PALETTE
from bluemira.builders.tools import apply_component_display_options
from bluemira.geometry.wire import BluemiraWire
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.params import BluemiraSTParams
import numpy as np


@dataclass
class ISBuilderParams(ParameterFrame):
    """Parameters for building an inboard shield"""
    # radial build parameters
    n_TF: Parameter[int]
    r_cs_in: Parameter[float]
    tk_cs: Parameter[float]
    tk_tf_inboard: Parameter[float]
    g_ts_tf: Parameter[float]
    tk_ts: Parameter[float]
    g_vv_ts: Parameter[float]
    tk_vv_in: Parameter[float]
    tk_sh_in: Parameter[float]


class ISBuilder(Builder):
    """Builder for the inboard shield."""

    IS = "IS"
    param_cls: type[ISBuilderParams] = ISBuilderParams
    params: ISBuilderParams


    def __init__(
        self,
        params: ISBuilderParams,
        build_config: dict,
        material_name: str,
        ref_fbe: Equilibrium,
    ):
        super().__init__(params, {"material": {self.IS: material_name}})
        self.ref_fbe = ref_fbe

    def radial_build_inboard_shield(self, build_config: dict) -> None:
        radial_build_list = [self.params.r_cs_in.value, self.params.tk_cs.value, 
                                self.params.tk_tf_inboard.value, self.params.g_ts_tf.value, 
                                self.params.tk_ts.value, self.params.g_vv_ts.value, 
                                self.params.tk_vv_in.value, self.params.tk_sh_in.value]
        radial_build_to_shield = np.sum(radial_build_list)
        return radial_build_to_shield
    
    def build(self,

               ) -> Component:
        """Build the inboard shield component."""
        # pass in fbe - to be removed once shield design more mature
        # pass in required flux surfaces only.
        radial_shield_position = self.radial_build_inboard_shield(self.build_config)
        ref_fbe = self.ref_fbe
        n_sectors = self.build_config.get("n_sectors", 1)
        sector_degree = 360.0 / self.params.n_TF.value
        o_points,x_points = ref_fbe.get_OX_points()
        x_point_coords = np.array([[xp.x, xp.z] for xp in x_points])
        if len(x_points) == 0:
            raise ValueError("No X points found in the plasma boundary, cannot build inboard shield.")

        # make inboard shield geometry
        # create vertical wire joining lower and upper x points 
        shield_wire_coords = Coordinates({"x":[x_point_coords[0][0],x_point_coords[0][0]],
                                    "z":[x_point_coords[0][1],x_point_coords[1][1]]})
        
        shield_wire_outer = make_polygon(shield_wire_coords, label="Shield wire outer")
        shield_wire_outer.translate(((-x_point_coords[0][0] + radial_shield_position),0,0))
        shield_wire_inner = shield_wire_outer.deepcopy()
        shield_wire_inner.translate((-self.params.tk_sh_in.value, 0, 0))


        shield_top_cap_wire = make_polygon([(shield_wire_outer.start_point(), shield_wire_inner.start_point())], label="Shield top cap wire")
        shield_bottom_cap_wire = make_polygon([(shield_wire_outer.end_point(), shield_wire_inner.end_point())], label="Shield bottom cap wire")
        shield_loop = BluemiraWire([shield_wire_outer, shield_top_cap_wire, shield_wire_inner, shield_bottom_cap_wire], label="Shield loop")
        shield_face = BluemiraFace(shield_loop, label="Shield face")
        shield_xyz = revolve_shape(shield_face, base=(0, 0, 0), direction=(0, 0, 1), degree=sector_degree * n_sectors, label="shield revolved")
        shield_xz = shield_face
        mat = self.get_material(self.IS)

        pc_xz = PhysicalComponent("Inboard shield",shield_xz,mat)
        pc_xyz = PhysicalComponent("Inboard shield",shield_xyz,mat)

        return self.component_tree(xz=[pc_xz], xy=[], xyz=[pc_xyz])