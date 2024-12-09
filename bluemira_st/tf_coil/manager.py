# SPDX-FileCopyrightText: 2024-present 2024-present The Bluemira Team <oliver.funk@ukaea.co.uk>
#
# SPDX-License-Identifier: MIT
"""TFCoil component manager."""

from bluemira.base.reactor import ComponentManager


class TFCoil(ComponentManager):
    """TF Coil component manager."""

    def wp_volume(self) -> float:
        """Get winding pack volume."""
        return (
            self.component()
            .get_component("xyz")
            .get_component("Winding pack")
            .shape.volume()
        )
