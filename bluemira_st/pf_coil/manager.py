# SPDX-FileCopyrightText: 2024-present 2024-present The Bluemira Team 

# SPDX-License-Identifier: MIT
"""PFCoil component manager."""

from bluemira.base.reactor import ComponentManager

# update with PF relevant methods
class PFCoil(ComponentManager):
    """PF Coil component manager."""
    def pf_function(self) -> float:
        """Get something relevant to PF coil design."""
        return (
            self.component()
        )