from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from bluemira.equilibria import Equilibrium
from bluemira.geometry.constants import VERY_BIG
from bluemira.geometry.face import BluemiraFace
from bluemira.geometry.tools import (
    boolean_cut,
    distance_to,
    make_polygon,
    offset_wire,
    split_wire,
)

from bluemira_st.optimisation.magnectic_constrains import make_auto_lcfs_constraint

if TYPE_CHECKING:
    from bluemira.base.parameter_frame import ParameterFrame
    from bluemira.equilibria.optimisation.constraints import MagneticConstraint
    from bluemira.geometry.parameterisations import GeometryParameterisation
    from bluemira.geometry.wire import BluemiraWire

import numpy as np
from bluemira.base.look_and_feel import bluemira_warn
from bluemira.equilibria.grid import Grid
from bluemira.equilibria.optimisation.constraints import (
    FieldNullConstraint,
    IsofluxConstraint,
    MagneticConstraintSet,
    PsiBoundaryConstraint,
)
from bluemira.equilibria.shapes import flux_surface_johner
from bluemira.geometry.coordinates import Coordinates, interpolate_points


def build_reference_constraint_set(
    constraint_config: dict, lcfs_coords: Coordinates
) -> MagneticConstraintSet:
    """
    Build a set of reference constraints for the equilibrium.

    Parameters
    ----------
    constraint_config:
        Configuration for the constraints
    lcfs_coords:
        Coordinates of the LCFS (discretised)

    Returns
    -------
    ReferenceConstraints:
        Set of reference constraints for the equilibrium
    """
    z_min = np.min(lcfs_coords.z)
    z_max = np.max(lcfs_coords.z)
    arg_z_min = np.argmin(lcfs_coords.z)
    arg_z_max = np.argmax(lcfs_coords.z)

    constraints: list[MagneticConstraint]

    if np.isclose(abs(z_min), z_max):
        # Double null
        constraints = [
            FieldNullConstraint(lcfs_coords.x[arg_z_min], lcfs_coords.z[arg_z_min]),
            FieldNullConstraint(lcfs_coords.x[arg_z_max], lcfs_coords.z[arg_z_max]),
        ]
    else:
        # Single null
        constraints = [
            FieldNullConstraint(lcfs_coords.x[arg_z_min], lcfs_coords.z[arg_z_min])
            if abs(z_min) > z_max
            else FieldNullConstraint(lcfs_coords.x[arg_z_max], lcfs_coords.z[arg_z_max]),
        ]

    lcfs_iso_flux_const = make_auto_lcfs_constraint(
        constraint_config, x_lcfs=lcfs_coords.x, z_lcfs=lcfs_coords.z
    )
    constraints.append(lcfs_iso_flux_const)

    return MagneticConstraintSet(constraints)


def get_intersections_from_angles(
    boundary: BluemiraWire, ref_x: float, ref_z: float, angles: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Get the intersections of a boundary with lines defined by angles.

    Parameters
    ----------
    boundary:
        Boundary to intersect with

    ref_x:
        Reference x coordinate
    ref_z:
        Reference z coordinate
    angles:
        Angles to use to define the lines

    Returns
    -------
    :
        Intersections of the boundary with the lines defined by the angles
    """
    n_angles = len(angles)
    x_c, z_c = np.zeros(n_angles), np.zeros(n_angles)
    for i, angle in enumerate(angles):
        line = make_polygon([
            [ref_x, ref_x + VERY_BIG * np.cos(angle)],
            [0, 0],
            [ref_z, ref_z + VERY_BIG * np.sin(angle)],
        ])
        _, intersection = distance_to(boundary, line)
        x_c[i], _, z_c[i] = intersection[0][0]
    return x_c, z_c


def plasma_data(eq: Equilibrium) -> dict[str, float]:
    """
    Extract and return plasma data from an equilibrium object.

    Returns
    -------
    :
        Plasma data extracted from the equilibrium object
    """
    p_dat = eq.analyse_plasma()
    return {
        "beta_p": p_dat.beta_p,
        "delta_95": p_dat.delta_95,
        "delta": p_dat.delta,
        "I_p": p_dat.I_p,
        "kappa_95": p_dat.kappa_95,
        "kappa": p_dat.kappa,
        "l_i": p_dat.li,
        "q_95": p_dat.q_95,
        "shaf_shift": np.hypot(p_dat.dx_shaf, p_dat.dz_shaf),
    }
