# SPDX-FileCopyrightText: 2024-present The Bluemira Team <oliver.funk@ukaea.co.uk>
#
# SPDX-License-Identifier: MIT

"""The reactor design example."""

# %%
from pathlib import Path
from typing import Union

from bluemira.base.designer import run_designer
from bluemira.base.parameter_frame import EmptyFrame
from bluemira.base.reactor import Reactor
from bluemira.base.reactor_config import ReactorConfig
from bluemira.builders.plasma import Plasma

from bluemira_st.build_routines import build_plasma, build_reference_equilibrium
from bluemira_st.equlibria.designer import DummyFixedEquilibriumDesigner
from bluemira_st.params import BluemiraSTParams
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.tf_coil.builder import TFCoilBuilder
from bluemira_st.tf_coil.designer import TFCoilDesigner
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

    lcfs_coords, profiles = run_designer(
        DummyFixedEquilibriumDesigner,
        reactor_config.params_for("Dummy fixed boundary equilibrium"),
        reactor_config.config_for("Dummy fixed boundary equilibrium"),
    )

    # reactor.equilibria = EquilibriumManager()

    reference_eq = build_reference_equilibrium(
        reactor_config.params_for("Free boundary equilibrium"),
        reactor_config.config_for("Free boundary equilibrium"),
        lcfs_coords,
        profiles,
    )

    reactor = MyReactor(
        "Bluemira Spherical Tokamak Example",
        n_sectors=reactor_config.global_params.n_TF.value,
    )

    reactor.plasma = build_plasma(
        reactor_config.params_for("Plasma"),
        reactor_config.config_for("Plasma"),
        reference_eq,
    )
    # %% [markdown]
    #
    # We create our TF coil

    # %%
    tf_coil_designer = TFCoilDesigner(
        plasma.lcfs(),
        None,
        reactor_config.config_for("TF Coil", "designer"),
    )
    tf_parameterisation = tf_coil_designer.execute()

    tf_coil_builder = TFCoilBuilder(
        reactor_config.params_for("TF Coil", "builder"),
        tf_parameterisation.create_shape(),
    )
    tf_coil = TFCoil(tf_coil_builder.build())

    # %% [markdown]
    #
    # Finally we add the components to the reactor and show the CAD

    # %%

    reactor.plasma = plasma
    reactor.tf_coil = tf_coil

    reactor.show_cad(n_sectors=1)
    reactor.show_cad("xz")

    return reactor
