# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

import numpy as np
from bluemira.base.builder import Builder
from bluemira.base.components import Component, ComponentT, PhysicalComponent
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.base.reactor import ComponentManager
from bluemira.builders.tools import apply_component_display_options
from bluemira.display import plot_2d
from bluemira.display.palettes import BLUE_PALETTE
from bluemira.display.plotter import PlotOptions
from bluemira.equilibria.coils._grouping import CoilSet
from bluemira.geometry.face import BluemiraFace
from bluemira.geometry.optimisation import GeomOptimisationProblem
from bluemira.geometry.optimisation._optimise import (
    GeomOptimiserResult,
)
from bluemira.geometry.optimisation.typed import GeomConstraintT
from bluemira.geometry.parameterisations import (
    GeometryParameterisation,
    PictureFrame,
)
from bluemira.geometry.tools import (
    distance_to,
    make_polygon,
    offset_wire,
    sweep_shape,
)
from bluemira.geometry.wire import BluemiraWire
from matplotlib import pyplot as plt


class ContractLengthByPortGOP(GeomOptimisationProblem):
    """Geometry optimisation problem to minimise a shape's length."""

    def __init__(
        self,
        ineq_constraints: list[GeomConstraintT],
    ):
        self._ineq_constraints = ineq_constraints

    def objective(self, geom: GeometryParameterisation) -> float:
        """Objective function to minimise."""
        return geom.create_shape().length

    def ineq_constraints(self) -> list[GeomConstraintT]:
        """List of inequality constraints to satisfy."""
        return self._ineq_constraints


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

    # PF params for spacing
    tk_pf_insulation: Parameter[float]
    tk_pf_casing: Parameter[float]
    r_pf_corner: Parameter[float]

    # Port params
    min_port_surface_area: Parameter[float]
    """Minimum surface area of the port"""
    min_plasma_dist: Parameter[float]
    """Minimum distance between the tf and the plasma"""
    g_tf_port: Parameter[float]
    """Gap between the TF coil (wp) and the port"""
    port_ob_inset: Parameter[float]
    """Port outboard inset, inset from tf_r_max"""
    port_ib_inset: Parameter[float]
    """Port inboard inset, inset from tf_r_start"""


def port_area_constraint(
    geom: GeometryParameterisation,
    min_port_surface_area: float,
    n_TF: int,
    total_g_tf_cl_port: float,
    port_ob_inset: float,
    port_ib_inset: float,
):
    """A constraint to maintain a minimum area of the port."""
    shape = geom.create_shape()

    tf_alpha = 360 / n_TF

    port_r_start = shape.bounding_box.x_min + port_ib_inset
    port_r_end = shape.bounding_box.x_max - port_ob_inset

    port_ib_y = np.sin(np.radians(tf_alpha / 2)) * port_r_start - total_g_tf_cl_port
    port_ob_y = np.sin(np.radians(tf_alpha / 2)) * port_r_end - total_g_tf_cl_port

    port_wire = make_polygon(
        [
            [port_r_start, port_ib_y, 0],
            [port_r_end, port_ob_y, 0],
            [port_r_end, -port_ob_y, 0],
            [port_r_start, -port_ib_y, 0],
        ],
        closed=True,
    )
    port_face = BluemiraFace(port_wire)

    # we want port_face.area >= min_port_surface_area,
    # optimiser wants constraint =< 0,
    # therefore, we negate the constraint:
    # -> -port_face.area <= -min_port_surface_area
    # -> min_port_surface_area - port_face.area <= 0

    return min_port_surface_area - port_face.area, port_wire


def plasma_min_length_constraint(
    geom: GeometryParameterisation, boundary: BluemiraWire, min_distance: float
):
    """A constraint to maintain a minimum distance between the TF coil and the plasma."""
    shape = geom.create_shape()
    return min_distance - distance_to(shape, boundary)[0]


class TFCoilDesigner(Designer[tuple[GeometryParameterisation, BluemiraWire]]):
    """TF coil shape designer."""

    params = TFCoilDesignerParams
    param_cls: type[TFCoilDesignerParams] = TFCoilDesignerParams

    def __init__(
        self,
        params: dict | ParameterFrame,
        build_config: dict,
        coilset: CoilSet,
        lcfs: BluemiraWire,
    ):
        super().__init__(params, build_config)
        self.lcfs = lcfs
        self.coilset = coilset

    def _get_parameterisation(self) -> PictureFrame:
        x_min = self.params.r_tf_in_centre.value
        ri = self.params.r_tf_corner_inner.value
        ro = self.params.r_tf_corner_outer.value
        offset = (
            self.params.g_pf_tf.value
            + self.params.tk_pf_casing.value
            + self.params.tk_pf_insulation.value
            + 0.5 * self.params.tf_wp_width.value
        )
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

    def _port_silhouette(self, geom: GeometryParameterisation) -> BluemiraWire:
        h_tf_wp_d = self.params.tf_wp_depth.value / 2

        port_wire = port_area_constraint(
            geom,
            min_port_surface_area=self.params.min_port_surface_area.value,
            n_TF=self.params.n_TF.value,
            total_g_tf_cl_port=self.params.g_tf_port.value + h_tf_wp_d,
            port_ob_inset=self.params.port_ob_inset.value,
            port_ib_inset=self.params.port_ib_inset.value,
        )[1]
        tf = geom.create_shape()
        port_wire.translate((0, 0, tf.bounding_box.z_max))
        return port_wire

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

    def _plot_post_opt(
        self, pre_opt_geom: GeometryParameterisation, result: GeomOptimiserResult
    ):
        pre_opt_cl = pre_opt_geom.create_shape()
        post_opt_cl = result.geom.create_shape()

        ax = plot_2d(pre_opt_cl, show=False)
        ax.set_title("Pre (black) and post (blue) optimisation centre lines")
        geom = self._get_parameterisation()
        for i, (x, _) in enumerate(result.history):
            geom.variables.set_values_from_norm(x)
            wire = geom.create_shape()
            wire_options = {
                "alpha": 0.5 + ((i + 1) / len(result.history)) / 2,
                "color": "red",
                "linewidth": 0.1,
            }
            ax = plot_2d(
                wire, options=PlotOptions(wire_options=wire_options), ax=ax, show=False
            )
        plot_2d(
            BluemiraFace(self.lcfs),
            ax=ax,
            options=PlotOptions(face_options={"color": "pink"}),
            show=False,
        )
        plot_2d(
            post_opt_cl,
            ax=ax,
            options=PlotOptions(wire_options={"color": "blue"}),
            show=True,
        )

    def run(self) -> tuple[GeometryParameterisation, BluemiraWire]:

        h_tf_wp_d = self.params.tf_wp_depth.value / 2
        parameterisation = self._get_parameterisation()
        wp_cross_section = self._make_wp_xs(self.params.r_tf_in_centre.value)

        geom_opt = ContractLengthByPortGOP([
            {
                "f_constraint": lambda geom: port_area_constraint(
                    geom,
                    min_port_surface_area=self.params.min_port_surface_area.value,
                    n_TF=self.params.n_TF.value,
                    total_g_tf_cl_port=self.params.g_tf_port.value + h_tf_wp_d,
                    port_ob_inset=self.params.port_ob_inset.value,
                    port_ib_inset=self.params.port_ib_inset.value,
                )[0],
                "tolerance": np.array([1e-8]),
            },
            {
                "f_constraint": lambda geom: plasma_min_length_constraint(
                    geom,
                    min_distance=self.params.min_plasma_dist.value,
                    boundary=self.lcfs,
                ),
                "tolerance": np.array([1e-8]),
            },
        ])

        initial_geom = parameterisation
        pre_opt_cl = initial_geom.create_shape()

        ax = plot_2d(
            [pre_opt_cl, BluemiraFace(self.lcfs)],
            options=[
                PlotOptions(
                    wire_options={"label": "TF centre line"},
                ),
                PlotOptions(
                    face_options={"color": "pink", "label": "Plasma"},
                ),
            ],
            show=False,
        )
        ax.set_title("Initial centre line and plasma boundary")
        ax.legend()
        plt.show()

        result = geom_opt.optimise(
            initial_geom,
            algorithm=self.build_config.get("algorithm", "COBYLA"),
            keep_history=True,
            opt_conditions={"ftol_abs": 1e-6},
        )

        self._plot_post_opt(initial_geom, result)

        return result.geom, self._port_silhouette(result.geom)


class TFCoilBuilder(Builder):
    """Build a 3D model of a TF Coil from a given centre line."""

    # just for this example
    params: TFCoilDesignerParams
    param_cls = TFCoilDesignerParams

    WINDING_PACK = "Winding pack"
    WP_INBOARD = "inboard WP"
    WP_OUTBOARD = "outboard WP"

    def __init__(self, params, centreline: BluemiraWire):
        super().__init__(params, {})
        self.centreline = centreline

    def make_tf_wp_xs(self) -> BluemiraWire:
        """Make a wire for the cross-section of the winding pack in xy."""
        h_width = self.params.tf_wp_width.value / 2
        h_depth = self.params.tf_wp_depth.value / 2
        return make_polygon(
            [
                [h_depth, h_width, 0],
                [h_depth, -h_width, 0],
                [-h_depth, -h_width, 0],
                [-h_depth, h_width, 0],
            ],
            closed=True,
        )

    def build(self) -> Component:
        """Run the full build for the TF coils."""
        return self.component_tree(
            xz=[self.build_xz()],
            xy=[self.build_xy()],
            xyz=[self.build_xyz()],
        )

    def build_xy(self) -> Component:
        """Build xy component"""
        wp_xs_ib = self.make_tf_wp_xs()
        wp_xs_ob = wp_xs_ib.deepcopy()
        wp_xs_ib.translate((self.centreline.bounding_box.x_min, 0, 0))
        wp_xs_ob.translate((self.centreline.bounding_box.x_max, 0, 0))
        return Component(
            self.WINDING_PACK,
            children=[
                PhysicalComponent(self.WP_INBOARD, wp_xs_ib),
                PhysicalComponent(self.WP_OUTBOARD, wp_xs_ob),
            ],
        )

    def build_xz(self) -> PhysicalComponent:
        """Build the xz Component of the TF coils."""
        inner = offset_wire(self.centreline, -self.params.tf_wp_depth.value / 2)
        outer = offset_wire(self.centreline, self.params.tf_wp_depth.value / 2)
        return PhysicalComponent(self.WINDING_PACK, BluemiraFace([outer, inner]))

    def build_xyz(self) -> PhysicalComponent:
        """Build the xyz Component of the TF coils."""
        wp_xs = self.make_tf_wp_xs()
        wp_xs.translate((self.centreline.bounding_box.x_min, 0, 0))
        volume = sweep_shape(wp_xs, self.centreline)
        comp = PhysicalComponent(self.WINDING_PACK, volume)
        apply_component_display_options(comp, color=BLUE_PALETTE["TF"][1])
        return comp


class TFCoil_with_port(ComponentManager):
    """TF coil component manager."""

    def __init__(self, component_tree: ComponentT, port_face: BluemiraWire) -> None:
        self._component = component_tree
        self.port_face = port_face


def build_tf_coils_for_port(
    params: dict, build_config: dict, coilset: CoilSet, plasma_lcfs: BluemiraWire
) -> TFCoil_with_port:
    """Build a TF coil from a set of parameters."""
    tf_coil_designer = TFCoilDesigner(
        params,
        build_config,
        lcfs=plasma_lcfs,
        coilset=coilset,
    )
    tf_coil_parameterisation, up_face = tf_coil_designer.execute()

    tf_coil_builder = TFCoilBuilder(
        params,
        tf_coil_parameterisation.create_shape(),
    )
    return TFCoil_with_port(tf_coil_builder.build(), up_face)
