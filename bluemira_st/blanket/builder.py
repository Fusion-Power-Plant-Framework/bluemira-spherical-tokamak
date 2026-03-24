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
from bluemira.geometry.coordinates import Coordinates
from bluemira.builders.tools import get_n_sectors

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

    # thicknesses
    tk_bb_ob: Parameter[float]
    n_TF: Parameter[int]
    fw_psi_n: Parameter[float]


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
        blanket_inner_surface = ref_fbe.get_flux_surface(self.params.fw_psi_n.value)

        blanket_inner_surface_wire = interpolate_bspline(
            Coordinates({"x": blanket_inner_surface.x, "z": blanket_inner_surface.z}),
            closed=False,
            label="Blanket inner surface wire",
        )
        # copy blanket inner surface wire and split in the same way as inner surface wire
        blanket_outer_surface_wire = interpolate_bspline(
            Coordinates({
                "x": blanket_inner_surface.x[::-1],
                "z": blanket_inner_surface.z[::-1],
            }),
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
        # create parameter to extend wire from x point to blanket inner surface

        x_cut_offset = 10.0
        z_cut_offset = 10.0
        upper_cut_box = BluemiraFace(
            make_polygon(
                {
                    "x": [
                        x_point_coords[1][0],
                        x_point_coords[1][0] + x_cut_offset,
                        x_point_coords[1][0] + x_cut_offset,
                        x_point_coords[1][0],
                    ],
                    "z": [
                        x_point_coords[1][1],
                        x_point_coords[1][1],
                        x_point_coords[1][1] + z_cut_offset,
                        x_point_coords[1][1] + z_cut_offset,
                    ],
                },
                closed=True,
            )
        )
        lower_cut_box = BluemiraFace(
            make_polygon(
                {
                    "x": [
                        x_point_coords[0][0],
                        x_point_coords[0][0] + x_cut_offset,
                        x_point_coords[0][0] + x_cut_offset,
                        x_point_coords[0][0],
                    ],
                    "z": [
                        x_point_coords[0][1],
                        x_point_coords[0][1],
                        x_point_coords[0][1] - z_cut_offset,
                        x_point_coords[0][1] - z_cut_offset,
                    ],
                },
                closed=True,
            )
        )

        # Boolean cut for blanket wires
        blanket_face_cut = boolean_cut(blanket_face, [upper_cut_box, lower_cut_box])
        blanket_face_final = blanket_face_cut[0]
        bb = revolve_shape(
            blanket_face_final,
            base=(0, 0, 0),
            direction=(0, 0, 1),
            degree=sector_degree * n_sectors,
            label="Blanket revolved",
        )
        bb_xz = blanket_face_final
        mat = self.get_material(self.BB)
        pc_xz = PhysicalComponent(self.BB,bb_xz, mat)
        pc_xyz = PhysicalComponent(self.BB, bb, mat)
        apply_component_display_options(pc_xyz, color=BLUE_PALETTE["BB"][0])


        # make inboard shield geometry
        # create vertical wire joining lower and upper x points 
        shield_wire_coords = Coordinates({"x":[x_point_coords[0][0],x_point_coords[0][0]],
                                    "z":[x_point_coords[0][1],x_point_coords[1][1]]})
        # find min x of lcfs
        # this probably should be done in a more robust way
        lcfs_min = np.min(lcfs_surface[0])
        shield_wire_outer = make_polygon(shield_wire_coords, label="Shield wire outer") 
        # translate shield wire in x direction so that it is just outside the lcfs
        shield_wire_outer.translate((-(x_point_coords[0][0]-lcfs_min+self.params.inboard_plasma_gap.value), 0, 0))
        shield_wire_inner =shield_wire_outer.deepcopy()
        shield_wire_inner.translate((self.params.shield_thickness.value, 0, 0))
        shield_top_cap_wire = make_polygon([(shield_wire_outer.start_point(), shield_wire_inner.start_point())], label="Shield top cap wire")
        shield_bottom_cap_wire = make_polygon([(shield_wire_outer.end_point(), shield_wire_inner.end_point())], label="Shield bottom cap wire")
        shield_loop = BluemiraWire([shield_wire_outer, shield_top_cap_wire, shield_wire_inner, shield_bottom_cap_wire], label="Shield loop")
        shield_face = BluemiraFace(shield_loop, label="Shield face")
        shield_xyz = revolve_shape(shield_face, base=(0, 0, 0), direction=(0, 0, 1), degree=sector_degree * n_sectors, label="shield revolved")
        shield_xz = shield_face
        pc_2_xz = PhysicalComponent("Inboard shield",shield_xz,mat)
        pc_2_xyz = PhysicalComponent("Inboard shield",shield_xyz,mat)
        apply_component_display_options(pc_2_xyz, color=BLUE_PALETTE["BB"][0])
        apply_component_display_options(pc_2_xz, color=BLUE_PALETTE["BB"][0])

        # component group for blanket and shield
        xz_group = Component("XZ_Group")
        pc_xz.parent = xz_group
        pc_2_xz.parent = xz_group

        xyz_group = Component("XYZ_Group")
        pc_xyz.parent = xyz_group
        pc_2_xyz.parent = xyz_group

        # Build the component tree
        # return component group
        return self.component_tree(
            xz=[xz_group],
            xy=[],
            xyz=[xyz_group]
        )
