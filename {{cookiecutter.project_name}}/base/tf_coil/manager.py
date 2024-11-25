# SPDX-FileCopyrightText: 2024-present {{cookiecutter.copyright_yr}}-present {{ cookiecutter.author_name }} <{{ cookiecutter.author_email }}>
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
