from __future__ import annotations

import numpy as np
from bluemira.equilibria.optimisation.constraints import (
    IsofluxConstraint,
)
from bluemira.geometry.coordinates import (
    Coordinates,
    coords_plane_intersect,
)
from bluemira.geometry.plane import BluemiraPlane


def make_auto_lcfs_constraint(
    constraint_config: dict,
    *,
    x_lcfs: np.ndarray,
    z_lcfs: np.ndarray,
) -> IsofluxConstraint:
    """Returns a mixture of an isoflux constraint and field null constraints.

    The isoflux constraint is generated from the LCFS points, and the field null
    constraints are generated from the top and bottom points of the LCFS.
    """
    constraint_tolerance = constraint_config.get("tolerance", 0.000001)
    n_points = constraint_config.get("n_points", 20)
    force_midplane_to_zero = constraint_config.get("force_midplane_to_zero", True)

    # calc midplane z
    z_max, z_min = np.max(z_lcfs), np.min(z_lcfs)
    z_mid = (z_max + z_min) / 2
    if force_midplane_to_zero:
        z_mid = 0

    # find lcfs x intersects
    lcfs_coords = Coordinates(xyz_array={"x": x_lcfs, "z": z_lcfs})
    z_plane = BluemiraPlane(base=(0.0, 0.0, z_mid), axis=(0.0, 0.0, 1.0))
    x_intersects, _, __ = coords_plane_intersect(lcfs_coords, z_plane).T

    x_ref = np.min(x_intersects)
    z_ref = z_mid

    resampled_x_lcfs = np.interp(
        np.linspace(0, len(x_lcfs), n_points),
        np.arange(0, len(x_lcfs)),
        x_lcfs,
    )
    resampled_z_lcfs = np.interp(
        np.linspace(0, len(z_lcfs), n_points),
        np.arange(0, len(z_lcfs)),
        z_lcfs,
    )

    return IsofluxConstraint(
        x=resampled_x_lcfs,
        z=resampled_z_lcfs,
        ref_x=x_ref,
        ref_z=z_ref,
        tolerance=constraint_tolerance,
    )
