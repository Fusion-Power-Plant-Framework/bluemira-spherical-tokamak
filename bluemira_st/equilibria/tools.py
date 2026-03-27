from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from bluemira.equilibria.optimisation.constraints import (
    FieldNullConstraint,
    IsofluxConstraint,
    MagneticConstraintSet,
)
from bluemira.geometry.constants import VERY_BIG
from bluemira.geometry.tools import (
    distance_to,
    make_polygon,
)

from bluemira_st.equilibria.reference_values import (
    SHAF_SHIFT,
    Z_P1_RAW,
)

if TYPE_CHECKING:
    from bluemira.equilibria import Equilibrium
    from bluemira.geometry.wire import BluemiraWire


def build_reference_constraint_set(
    params: dict,
) -> MagneticConstraintSet:
    """
    Build a set of reference constraints for the equilibrium.

    Parameters
    ----------
    params:
        Parameters to construct the constraints from

    Returns
    -------
    ReferenceConstraints:
        Set of reference constraints for the equilibrium
    """
    R_0 = params.R_0.value  # noqa: N806
    A = params.A.value  # noqa: N806
    kappa = params.kappa.value
    delta = params.delta.value
    tk_bb = params.tk_bb.value

    # Reference values
    rshaf_shift = SHAF_SHIFT
    rz_p1_raw = Z_P1_RAW

    # minor radius
    R_a = R_0 / A  # noqa: N806
    shaf_shift = rshaf_shift * R_a

    # null coords
    Z_x = kappa * R_a  # noqa: N806
    R_x = R_0 - delta * R_a  # noqa: N806

    R_in = R_0 - R_a  # noqa: N806
    R_out = R_0 + R_a  # noqa: N806

    R_leg1 = R_0 + shaf_shift  # noqa: N806
    Z_leg = Z_x + rz_p1_raw  # noqa: N806
    R_leg2 = R_0 + R_a + tk_bb  # noqa: N806

    x_point_u = FieldNullConstraint(R_x, Z_x)
    x_point_l = FieldNullConstraint(R_x, -Z_x)

    isoflux = IsofluxConstraint(
        [R_x, R_x, R_in, R_out, R_leg1, R_leg1, R_leg2, R_leg2],
        [Z_x, -Z_x, 0.0, 0.0, Z_leg, -Z_leg, Z_leg, -Z_leg],
        R_x,
        Z_x,
        tolerance=1e-6,
    )

    constraints_list = [isoflux, x_point_u, x_point_l]

    return MagneticConstraintSet(constraints_list)


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
        "beta_p": p_dat.beta_p.value,
        "delta_95": p_dat.delta_95.value,
        "delta": p_dat.delta.value,
        "I_p": p_dat.I_p.value,
        "kappa_95": p_dat.kappa_95.value,
        "kappa": p_dat.kappa.value,
        "l_i": p_dat.li.value,
        "q_95": p_dat.q_95.value,
        "shaf_shift": np.hypot(p_dat.dx_shaf.value, p_dat.dz_shaf.value),
    }
