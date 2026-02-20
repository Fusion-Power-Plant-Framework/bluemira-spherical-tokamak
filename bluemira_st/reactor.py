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
    build_bb
)
from bluemira_st.equlibria.designer import DummyFixedEquilibriumDesigner
from bluemira_st.params import BluemiraSTParams
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.tf_coil.manager import TFCoil
from bluemira_st.blanket.manager import BB
from bluemira.base.file import get_bluemira_root
from bluemira.materials.cache import establish_material_cache

class MyReactor(Reactor):
    """A simple reactor with two components."""

    plasma: Plasma
    tf_coil: TFCoil
    blanket: BB
    # Models
    # equilibria: EquilibriumManager


def main(build_config: str | Path | dict) -> MyReactor:
    """Reactor function."""
    reactor_config = ReactorConfig(build_config, BluemiraSTParams)
    establish_material_cache([
        Path(get_bluemira_root(), "examples", "design", "design_materials.py")
        .resolve()
        .as_posix(),
        "matproplib",
    ])
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
    reactor.blanket = build_bb(
        reactor_config.params_for("blanket"),
        reactor_config.config_for("blanket"),
        lcfs_wire,
        mat_name="BB_BZ_MATERIAL",
        )

    reactor.show_cad()
    reactor.show_cad("xz")

    return reactor
