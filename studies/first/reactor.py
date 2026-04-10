# SPDX-FileCopyrightText: 2024-present The Bluemira Team
#
# SPDX-License-Identifier: MIT

"""The reactor design example."""

# %%
from pathlib import Path

from bluemira.base.file import get_bluemira_root
from bluemira.base.reactor import Reactor
from bluemira.base.reactor_config import ReactorConfig
from bluemira.builders.plasma import Plasma
from bluemira.geometry.tools import interpolate_bspline
from bluemira.materials.cache import establish_material_cache

from bluemira_st.blanket.manager import BB
from bluemira_st.build_routines import (
    build_bb,
    build_plasma,
    build_reference_equilibrium,
    build_tf_coils,
)
from bluemira_st.params import BluemiraSTParams
from bluemira_st.radial_build.run_process import radial_build
from bluemira_st.tf_coil.manager import TFCoil


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
    reactor = MyReactor(
        "Bluemira Spherical Tokamak Example",
        n_sectors=reactor_config.global_params.n_TF.value,
    )

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

    ref_fbe = build_reference_equilibrium(
        reactor_config.params_for("reference_fbe").global_params,
        reactor_config.config_for("reference_fbe"),
    )

    # Fine (it'll just digest whatever it gets from the reference equilibrium)
    reactor.plasma = build_plasma(
        reactor_config.params_for("plasma"),
        reactor_config.config_for("plasma"),
        ref_fbe,
    )

    # Needs work: We need a "PictureFrame" shape
    reactor.tf_coil = build_tf_coils(
        reactor_config.params_for("tf_coils"),
        reactor_config.config_for("tf_coils"),
        ref_fbe.coilset,
        interpolate_bspline(ref_fbe.get_LCFS(), closed=True),
    )
    reactor.blanket = build_bb(
        reactor_config.params_for("blanket"),
        reactor_config.config_for("blanket"),
        mat_name="BB_BZ_MATERIAL",
        ref_fbe=ref_fbe,
    )

    reactor.show_cad("xyz")
    reactor.show_cad("xz")

    return reactor


if __name__ == "__main__":
    build_config_path = Path(Path(__file__).parent, "config/config.json").resolve()
    reactor = main(build_config_path)
