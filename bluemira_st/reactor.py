# SPDX-FileCopyrightText: 2024-present The Bluemira Team <oliver.funk@ukaea.co.uk>
#
# SPDX-License-Identifier: MIT

"""The reactor design example."""

# %%
from pathlib import Path
from typing import Union

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

# %% [markdown]
#
# # Simplistic Reactor Design
#
# This example show hows to set up a simple reactor, consisting of a plasma and
# a single TF coil.
# The TF coil will be optimised such that its length is minimised,
# whilst maintaining a minimum distance to the plasma.
#
# To do this we'll run through how to set up the parameters for the build,
# how to define the `Builder`s and `Designer`s
# (including the optimisation problem) for the plasma and TF coil,
# and how to run the build with configurable parameters.
#


# %%
class MyReactor(Reactor):
    """A simple reactor with two components."""

    plasma: Plasma
    tf_coil: TFCoil

    # Models
    # equilibria: EquilibriumManager


def main(build_config: Union[str, Path, dict]) -> MyReactor:  # noqa: FA100
    """Main reactor function."""
    reactor_config = ReactorConfig(build_config, BluemiraSTParams)

    radial_build(
        reactor_config.params_for("radial_build").global_params,
        reactor_config.config_for("radial_build"),
    )

    lcfs_wire, profiles = run_designer(
        DummyFixedEquilibriumDesigner,
        reactor_config.params_for("dummy_fixed_boundary"),
        reactor_config.config_for("dummy_fixed_boundary"),
    )

    tf_initial_cl = build_initial_tf_centerline(
        reactor_config.params_for("tf_initial_centerline"),
        reactor_config.config_for("tf_initial_centerline"),
        lcfs_wire,
    )

    # reactor.equilibria = EquilibriumManager()

    ref_fbe = build_reference_equilibrium(
        reactor_config.params_for("reference_fbe"),
        reactor_config.config_for("reference_fbe"),
        lcfs_wire,
        profiles,
        tf_initial_cl,
    )

    reactor = MyReactor(
        "Bluemira Spherical Tokamak Example",
        n_sectors=reactor_config.global_params.n_TF.value,
    )

    reactor.plasma = build_plasma(
        reactor_config.params_for("plasma"),
        reactor_config.config_for("plasma"),
        ref_fbe,
    )
    reactor.tf_coil = build_tf_coils(
        reactor_config.params_for("tf_coil"),
        reactor_config.config_for("tf_coil"),
        tf_initial_cl,
        lcfs_wire,
    )

    reactor.show_cad()
    reactor.show_cad("xz")

    return reactor
