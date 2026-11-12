from dataclasses import dataclass

import marimo_cad as cad
import numpy as np
from bluemira.base.builder import Builder
from bluemira.base.components import Component, ComponentT, PhysicalComponent
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.base.reactor import ComponentManager, Reactor
from bluemira.base.reactor_config import ReactorConfig
from bluemira.builders.plasma import Plasma
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
    extrude_shape,
    interpolate_bspline,
    make_polygon,
    offset_wire,
    sweep_shape,
)
from bluemira.geometry.wire import BluemiraWire
from matplotlib import pyplot as plt

from bluemira_st.blanket.manager import BreedingBlanket
from bluemira_st.build_routines import (
    build_bb,
    build_is,
    build_pf_coils,
    build_plasma,
    build_reference_equilibrium,
    build_tf_coils,
)
from bluemira_st.inboard_shield.manager import IS
from bluemira_st.params import BluemiraSTParams
from bluemira_st.pf_coil.manager import PFCoil
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.tf_coil.manager import TFCoil


class ContractLengthByUpperPortGOP(GeomOptimisationProblem):
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
    """Minimum surface area of the upper port"""
    min_plasma_dist: Parameter[float]
    """Minimum distance between the tf and the plasma"""
    g_tf_up: Parameter[float]
    """Gap between the TF coil (wp) and the upper port"""
    up_ob_inset: Parameter[float]
    """Upper port outboard inset, inset from tf_r_max"""
    up_ib_inset: Parameter[float]
    """Upper port inboard inset, inset from tf_r_start"""


    def upper_port_area_constraint(
    geom: GeometryParameterisation,
    min_port_surface_area: float,
    n_TF: int,
    total_g_tf_cl_up: float,
    up_ob_inset: float,
    up_ib_inset: float,
    ):
    """A constraint to maintain a minimum area of the upper port."""
    shape = geom.create_shape()

    tf_alpha = 360 / n_TF

    up_r_start = shape.bounding_box.x_min + up_ib_inset
    up_r_end = shape.bounding_box.x_max - up_ob_inset

    up_ib_y = np.sin(np.radians(tf_alpha / 2)) * up_r_start - total_g_tf_cl_up
    up_ob_y = np.sin(np.radians(tf_alpha / 2)) * up_r_end - total_g_tf_cl_up

    up_wire = make_polygon(
        [
            [up_r_start, up_ib_y, 0],
            [up_r_end, up_ob_y, 0],
            [up_r_end, -up_ob_y, 0],
            [up_r_start, -up_ib_y, 0],
        ],
        closed=True,
    )
    up_face = BluemiraFace(up_wire)

    # we want up_face.area >= min_port_surface_area,
    # optimiser wants constraint =< 0,
    # therefore, we negate the constraint:
    # -> -up_face.area <= -min_port_surface_area
    # -> min_port_surface_area - up_face.area <= 0

    return min_port_surface_area - up_face.area, up_wire


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

    def _upper_port_silhouette(self, geom: GeometryParameterisation) -> BluemiraWire:
        h_tf_wp_d = self.params.tf_wp_depth.value / 2

        port_wire = upper_port_area_constraint(
            geom,
            min_port_surface_area=self.params.min_port_surface_area.value,
            n_TF=self.params.n_TF.value,
            total_g_tf_cl_up=self.params.g_tf_up.value + h_tf_wp_d,
            up_ob_inset=self.params.up_ob_inset.value,
            up_ib_inset=self.params.up_ib_inset.value,
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

        geom_opt = ContractLengthByUpperPortGOP([
            {
                "f_constraint": lambda geom: upper_port_area_constraint(
                    geom,
                    min_port_surface_area=self.params.min_port_surface_area.value,
                    n_TF=self.params.n_TF.value,
                    total_g_tf_cl_up=self.params.g_tf_up.value + h_tf_wp_d,
                    up_ob_inset=self.params.up_ob_inset.value,
                    up_ib_inset=self.params.up_ib_inset.value,
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

        return result.geom, self._upper_port_silhouette(result.geom)


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

    def __init__(
        self, component_tree: ComponentT, upper_port_face: BluemiraWire
    ) -> None:
        self._component = component_tree
        self.upper_port_face = upper_port_face
