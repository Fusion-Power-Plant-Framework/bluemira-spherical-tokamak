# SPDX-FileCopyrightText: 2024-present The Bluemira Team <oliver.funk@ukaea.co.uk>
#
# SPDX-License-Identifier: MIT

"""The reactor design example."""

# %%
from pathlib import Path

from bluemira.base.designer import run_designer
from bluemira.base.reactor import Reactor
from bluemira.base.reactor_config import ReactorConfig
from bluemira.builders.plasma import Plasma

from bluemira_st.build_routines import (
    build_initial_tf_centerline,
    build_plasma,
    build_reference_equilibrium,
    build_tf_coils,
)
from bluemira_st.equlibria.designer import DummyFixedEquilibriumDesigner
from bluemira_st.params import BluemiraSTParams
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.tf_coil.manager import TFCoil


class MyReactor(Reactor):
    """A simple reactor with two components."""

    plasma: Plasma
    tf_coil: TFCoil

    # Models
    # equilibria: EquilibriumManager


def main(build_config: str | Path | dict) -> MyReactor:
    """Reactor function."""
    reactor_config = ReactorConfig(build_config, BluemiraSTParams)
    reactor = MyReactor(
        "Bluemira Spherical Tokamak Example",
        n_sectors=reactor_config.global_params.n_TF.value,
    )

    # Done
    radial_build(
        reactor_config.params_for("radial_build").global_params,
        reactor_config.config_for("radial_build"),
    )

    # Needs work (LCFS is not great)
    lcfs_wire, profiles = run_designer(
        DummyFixedEquilibriumDesigner,
        reactor_config.params_for("dummy_fixed_boundary"),
        reactor_config.config_for("dummy_fixed_boundary"),
    )

    # We can remove; because we're gonna put the PF coils inside the TF coil
    tf_initial_cl = build_initial_tf_centerline(
        reactor_config.params_for("tf_initial_centerline"),
        reactor_config.config_for("tf_initial_centerline"),
        lcfs_wire,
    )

    # Make a simple equilibrium with arbitrary coils (as many as you want and
    # as close as necessary)
    ref_fbe = build_reference_equilibrium(
        reactor_config.params_for("reference_fbe"),
        reactor_config.config_for("reference_fbe"),
        lcfs_wire,
        profiles,
        tf_initial_cl,
    )

    # Fine (it'll just digest whatever it gets from the reference equilibrium)
    reactor.plasma = build_plasma(
        reactor_config.params_for("plasma"),
        reactor_config.config_for("plasma"),
        ref_fbe,
    )

    # Needs work: We need a "PictureFrame" shape
    reactor.tf_coil = build_tf_coils(
        reactor_config.params_for("tf_coil"),
        reactor_config.config_for("tf_coil"),
        tf_initial_cl,
        lcfs_wire,
    )

    # Optimise the PF coil currents / positions to get the desired plasma shape
    # # Optimise equilibrium
    # # Build the PF coils (just re-use the LAR build stage)

    # Oliver
    # Build the blankets:
    #   Some offset to the LCFS, and just chop top and bottom for the divertor regions
    #   Same thing on the inboard side, but with a rectangle.

    reactor.show_cad()
    reactor.show_cad("xz")

    return reactor
