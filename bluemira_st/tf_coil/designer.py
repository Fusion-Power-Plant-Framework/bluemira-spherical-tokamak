# SPDX-FileCopyrightText: 2024-present 2024-present The Bluemira Team <oliver.funk@ukaea.co.uk>
#
# SPDX-License-Identifier: MIT
"""TF Coil Designer."""

from dataclasses import dataclass

import numpy as np
from bluemira.base.designer import Designer
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.base.reactor_config import ConfigParams
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.optimisation import optimise_geometry
from bluemira.geometry.parameterisations import GeometryParameterisation, PrincetonD
from bluemira.geometry.tools import (
    distance_to,
    make_polygon,
)
from bluemira.geometry.wire import BluemiraWire
from bluemira.utilities.tools import get_class_from_module

# And now the TF Coil, in this instance for simplicity we are only making
# one TF coil.
#
# The TF coil designer finds the geometry parameterisation given in
# the `build_config` which should point to a class.
# The parameterisation is then fed into the optimiser that
# minimises the size of the TF coil, whilst keeping at least a meter away
# from the plasma at any point.
# Further information on geometry and geometry optimisations can be found in the
# [geometry tutorial](../geometry/geometry_tutorial.ex.py) and
# [geometry optimisation tutorial](../optimisation/geometry_optimisation.ex.py).
#


@dataclass
class TFInitialShapeDesignerParams(ParameterFrame):
    """
    Parameter frame for the initial TF center-line designer.
    """

    tf_cl_ib_x: Parameter[float]
    tf_cl_ob_x: Parameter[float]
    tf_tot_tk_y: Parameter[float]
    tf_tot_tk_z: Parameter[float]


class TFInitialShapeDesigner(Designer[tuple[PrincetonD, BluemiraWire]]):
    """
    Designer to create the initial TF coil centreline.

    Parameters
    ----------
    params:
        The parameters for the designer
    build_config:
        The config for the designer
    """

    params: TFInitialShapeDesignerParams
    param_cls: type[TFInitialShapeDesignerParams] = TFInitialShapeDesignerParams

    def __init__(
        self,
        params,
        build_config,
        lcfs_boundary: BluemiraWire,
    ):
        super().__init__(params, build_config)
        self.lcfs_boundary = lcfs_boundary

    def run(self) -> tuple[PrincetonD, BluemiraWire]:
        """
        Run the InitialTFCentrelineDesigner.

        Returns
        -------
        :
            The initial TF coil centreline
        """
        lcfs_coords = self.lcfs_boundary.discretise(byedges=True, ndiscr=200)
        lcfs_z_max = np.min(lcfs_coords.z)
        lcfs_z_min = np.max(lcfs_coords.z)
        cl_ib_x = self.params.tf_cl_ib_x.value
        cl_ob_x = self.params.tf_cl_ob_x.value
        prin_d = PrincetonD({
            "x1": {"value": cl_ib_x, "fixed": True},
            "dz": {"value": (lcfs_z_max + lcfs_z_min) / 2, "fixed": True},
            "x2": {
                "value": cl_ob_x,
                "lower_bound": cl_ob_x * 0.9,
                "upper_bound": cl_ob_x * 1.1,
            },
        })

        z_top = self.params.tf_tot_tk_z.value / 2
        y_right = self.params.tf_tot_tk_y.value / 2
        tf_face = make_polygon(
            {
                "x": 0,
                "y": [y_right, y_right, -y_right, -y_right],
                "z": [z_top, -z_top, -z_top, z_top],
            },
            closed=True,
        )
        return prin_d, tf_face


class TFCoilDesigner(Designer[GeometryParameterisation]):
    """TF coil shape designer."""

    param_cls = None  # This designer takes no parameters

    def __init__(
        self,
        plasma_lcfs: BluemiraWire,
        params: None,
        build_config: ConfigParams,
    ):
        super().__init__(params, build_config)
        self.lcfs = plasma_lcfs
        self.parameterisation_cls = get_class_from_module(
            self.build_config["param_class"],
            default_module="bluemira.geometry.parameterisations",
        )

    def run(self) -> GeometryParameterisation:
        """Run the design of the TF coil."""
        parameterisation = self.parameterisation_cls(
            var_dict=self.build_config["var_dict"],
        )
        min_dist_to_plasma = 1  # meter
        return self.minimise_tf_coil_size(parameterisation, min_dist_to_plasma)

    def minimise_tf_coil_size(
        self,
        geom: GeometryParameterisation,
        min_dist_to_plasma: float,
    ) -> GeometryParameterisation:
        """Run an optimisation to minimise the size of the TF coil.

        We're minimising the size of the coil whilst always keeping a
        minimum distance to the plasma.
        """
        distance_constraint = {
            "f_constraint": lambda g: self._constrain_distance(
                g,
                min_dist_to_plasma,
            ),
            "tolerance": np.array([1e-6]),
        }
        optimisation_result = optimise_geometry(
            geom=geom,
            f_objective=lambda g: g.create_shape().length,
            opt_conditions={"max_eval": 500, "ftol_rel": 1e-6},
            ineq_constraints=[distance_constraint],
        )
        return optimisation_result.geom

    def _constrain_distance(
        self,
        geom: BluemiraWire,
        min_distance: float,
    ) -> np.ndarray:
        return np.array(
            min_distance - distance_to(geom.create_shape(), self.lcfs)[0],
        )
