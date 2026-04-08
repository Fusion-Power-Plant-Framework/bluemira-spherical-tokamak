"""Breeder Blanket (BB) Builder."""

from dataclasses import dataclass

import numpy as np
from bluemira.base.builder import Builder
from bluemira.base.components import Component, PhysicalComponent
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.builders.tools import apply_component_display_options
from bluemira.display.palettes import BLUE_PALETTE
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.face import BluemiraFace
from bluemira.geometry.tools import (
    boolean_cut,
    interpolate_bspline,
    make_polygon,
    revolve_shape,
)
from bluemira.geometry.wire import BluemiraWire


@dataclass
class BBBuilderParams(ParameterFrame):
    """Parameters for building a breeder blanket."""

    # gaps
    g_p_bb: Parameter[float]
    g_bb_tf_min: Parameter[float]
    # thicknesses
    tk_bb_ob: Parameter[float]
    n_TF: Parameter[int]


class BBBuilder(Builder):
    """Builder for the breeder blanket."""

    BB = "BB"
    param_cls: type[BBBuilderParams] = BBBuilderParams
    params: BBBuilderParams

    def __init__(
        self,
        params: BBBuilderParams,
        build_config: dict,  # noqa: ARG002
        material_name: str,
        ref_fbe: Equilibrium,
    ):
        super().__init__(params, {"material": {self.BB: material_name}})
        self.ref_fbe = ref_fbe

    def build(
        self,
    ) -> Component:
        """Build the breeder blanket component."""
        # pass in fbe - to be removed once blanket design more mature
        # pass in required flux surfaces only.
        ref_fbe = self.ref_fbe
        n_sectors = self.build_config.get("n_sectors", 1)

        sector_degree = 360.0 / self.params.n_TF.value

        _, x_points = ref_fbe.get_OX_points()
        # Only select the two "active" nulls
        x_point_coords = np.array([[xp.x, xp.z] for xp in x_points[:2]])
        # Sort them bottom to top
        x_point_coords = x_point_coords[np.argsort(x_point_coords[:, 1])]

        # get flux surface just outside the LCFS
        blanket_inner_surface = ref_fbe.get_flux_surface(1.05)
        # create parameter to extend wire from x point to blanket inner surface
        x_width = (self.params.g_p_bb.value + self.params.tk_bb_ob.value) * 2
        x_point_wire_coords_upper = Coordinates({
            "x": [
                x_point_coords[1][0] + self.params.g_p_bb.value,
                x_point_coords[1][0] + self.params.g_p_bb.value + x_width,
            ],
            "z": [x_point_coords[1][1], x_point_coords[1][1]],
        })
        x_point_wire_coords_lower = Coordinates({
            "x": [
                x_point_coords[0][0] + self.params.g_p_bb.value,
                x_point_coords[0][0] + self.params.g_p_bb.value + x_width,
            ],
            "z": [x_point_coords[0][1], x_point_coords[0][1]],
        })

        x_point_wire_lower = make_polygon(
            x_point_wire_coords_lower, label="X-point wire 2"
        )

        # reverse x-point wire coordinates so wire directions are consistent
        # for creating faces etc.
        rev_coords_x_point = Coordinates({
            "x": list(reversed(x_point_wire_coords_upper.x)),
            "z": list(reversed(x_point_wire_coords_upper.z)),
        })

        # reverse blanket outer surface wire coords
        rev_coords = Coordinates({
            "x": list(reversed(blanket_inner_surface.x)),
            "z": list(reversed(blanket_inner_surface.z)),
        })

        x_point_wire_upper = make_polygon(
            rev_coords_x_point, label="reversed X-point wire"
        )

        blanket_inner_surface_wire = interpolate_bspline(
            Coordinates({"x": blanket_inner_surface.x, "z": blanket_inner_surface.z}),
            closed=False,
            label="Blanket inner surface wire",
        )
        # copy blanket inner surface wire and split in the same way as inner surface wire
        blanket_outer_surface_wire = interpolate_bspline(
            Coordinates({"x": rev_coords.x, "z": rev_coords.z}),
            closed=False,
            label="Blanket outer surface wire",
        )

        # translate outer blanket segments by tk_bb in x-direction
        blanket_outer_surface_wire.translate((self.params.tk_bb_ob.value, 0, 0))

        # create wires to join blanket end points
        upper_cap_wire = make_polygon(
            [
                (
                    blanket_inner_surface_wire.end_point(),
                    blanket_outer_surface_wire.start_point(),
                )
            ],
            label="Upper cap wire",
        )
        lower_cap_wire = make_polygon(
            [
                (
                    blanket_inner_surface_wire.start_point(),
                    blanket_outer_surface_wire.end_point(),
                )
            ],
            label="Lower cap wire",
        )

        blanket_loop = BluemiraWire(
            [
                blanket_inner_surface_wire,
                upper_cap_wire,
                blanket_outer_surface_wire,
                lower_cap_wire,
            ],
            label="Blanket loop",
        )
        blanket_face = BluemiraFace(blanket_loop, label="Blanket face")

        # Boolean cut for blanket face with x-point wires
        cut_box_top_wire = x_point_wire_upper.deepcopy()
        cut_box_bottom_wire = x_point_wire_lower.deepcopy()
        cut_box_top_wire.translate((0, 0, lower_cap_wire.bounding_box.z_max))
        cut_box_bottom_wire.translate((0, 0, upper_cap_wire.bounding_box.z_min))
        # create wires to make closed loops for boolean cut faces.
        cut_box_left_1 = make_polygon(
            [(x_point_wire_upper.start_point(), cut_box_top_wire.start_point())],
            label="Cut box top left",
        )
        cut_box_right_1 = make_polygon(
            [(x_point_wire_upper.end_point(), cut_box_top_wire.end_point())],
            label="Cut box bottom left",
        )
        cut_box_left_2 = make_polygon(
            [(x_point_wire_lower.start_point(), cut_box_bottom_wire.start_point())],
            label="Cut box top right",
        )
        cut_box_right_2 = make_polygon(
            [(x_point_wire_lower.end_point(), cut_box_bottom_wire.end_point())],
            label="Cut box bottom right",
        )
        # cutting boxes for boolean cut of flux surfaces sued to create blanket shape.
        upper_cut_box_wire = BluemiraWire(
            [cut_box_top_wire, cut_box_right_1, x_point_wire_upper, cut_box_left_1],
            label="Cut box wire",
        )
        upper_cut_box_face = BluemiraFace(upper_cut_box_wire)
        lower_cut_box_wire = BluemiraWire(
            [cut_box_bottom_wire, cut_box_right_2, x_point_wire_lower, cut_box_left_2],
            label="Cut box wire",
        )
        lower_cut_box_face = BluemiraFace(lower_cut_box_wire)
        # Boolean cut for blanket wires
        blanket_face_cut = boolean_cut(
            blanket_face, [upper_cut_box_face, lower_cut_box_face]
        )
        blanket_face_final = blanket_face_cut[1]
        bb = revolve_shape(
            blanket_face_final,
            base=(0, 0, 0),
            direction=(0, 0, 1),
            degree=sector_degree * n_sectors,
            label="Blanket revolved",
        )
        bb_xz = blanket_face_final
        mat = self.get_material(self.BB)
        pc_xz = PhysicalComponent(self.BB, bb_xz, mat)
        pc_xyz = PhysicalComponent(self.BB, bb, mat)
        apply_component_display_options(pc_xyz, color=BLUE_PALETTE["BB"][0])

        return self.component_tree(xz=[pc_xz], xy=[], xyz=[pc_xyz])
