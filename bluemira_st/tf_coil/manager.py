# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT
"""TFCoil component manager."""

from bluemira.base.reactor import ComponentManager
import numpy as np
import numpy.typing as npt
from bluemira.geometry.wire import BluemiraWire


class TFCoil(ComponentManager):
    """TF Coil component manager."""
    def __init__(self, component, field_solver, centreline):
        super().__init__(component)
        self._field_solver = field_solver
        self._centreline = centreline


    def wp_volume(self) -> float:
        """Get winding pack volume."""
        return (
            self
            .component()
            .get_component("xyz")
            .get_component("Winding pack")
            .shape.volume()
        )

    def field(
        self, x: npt.ArrayLike, y: npt.ArrayLike, z: npt.ArrayLike
    ) -> npt.NDArray[np.float64]:
        """
        Calculate the magnetic field due to the TF coils at a set of points.

        Parameters
        ----------
        x:
            The x coordinate(s) of the points at which to calculate the field
        y:
            The y coordinate(s) of the points at which to calculate the field
        z:
            The z coordinate(s) of the points at which to calculate the field

        Returns
        -------
        :
            The magnetic field vector {Bx, By, Bz} in [T]
        """
        return self._field_solver.field(x, y, z)
