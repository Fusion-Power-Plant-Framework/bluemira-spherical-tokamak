# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "matplotlib==3.11.2",
#     "numpy==2.5.4",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    # Copyright statement
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #Introduction
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
        ##Bluemira
        `Bluemira` is an integrated inter-disciplinary design tool for future fusion reactors. It incorporates several modules, some of which rely on other codes, to carry out a range of typical conceptual fusion reactor design activities.


        It is a 'medium fidelity' code, meaning it can build on lower fidelity codes like `PROCESS` and be used as parameterisations for higher fidelity codes, of which you can feed back changes and iterate designs.

        `Bluemira` is capable of optimising and caluclating various parts of fusion reactor and plant design, such as;
        - 🧲 placing and optimising Poloidal Field (PF) coils, including minimising the current
        - 🌡️ calculating heat loads of parts of the reactor
        - 💡 calculating the 'Balance of Plant' (BoP)
        - 🧲 optimising Toroidal Field (TF) coils to minimise ripple effects in the magnetic field of the plasma
        - 🪩 neutronics calculations, which helps us understand how long parts of the reactor will last before we need to replace them (e.g. blanket, divertor, magnets, first wall impacts etc.)
            - neutron wall loading
            - radiation loads
            - photon loads
            - charged particle loads
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Learning objectives

    - How we can optimise a design
    - Understand how Bluemira operates
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #Set-up
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Run the below cells to fetch relevant files from our GitHub repositories, install modules we need and establish a cache for the materials we'll need for our reactor.

    The majority of the code for this is specific for running `bluemira` and `bluemira spherical tokmakak example` in this marimo notebook, not running it generally. So we've hidden the code cells, but feel free to take a look if you wish!

    This set-up will take a couple of minutes.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Fetch relevant files
    """)


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    from fsspec.implementations.github import GithubFileSystem

    # establish access to the bluemira and bluemira spherical tokamak github repos
    bm = GithubFileSystem(
        org="Fusion-Power-Plant-Framework", repo="bluemira", branch="main"
    )
    bm_st = GithubFileSystem(
        org="Fusion-Power-Plant-Framework",
        repo="bluemira-spherical-tokamak",
        sha="7de21ca",
    )

    # we download the design_materials.py script from bluemira by specifying a path to download from
    # and then state where it is locally
    designmat_path = "github://examples/design/design_materials.py"
    designmat = bm.download(designmat_path, "")
    local_designmat_path = Path("design_materials.py")

    # and again for the bluemira spherical tokamak example
    INDAT_path = "github://studies/first/data/PROCESS/st_regression.IN.DAT"
    INDAT = bm_st.download(INDAT_path, "")
    local_indat_path = Path("st_regression.IN.DAT")

    TF_path = "github://studies/first/data/TF/TFCoilDesign.json"
    TF_json = bm_st.download(TF_path, "")
    return local_designmat_path, local_indat_path


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Install Bluemira and Bluemira Spherical Tokamak Example
    """)


@app.cell(hide_code=True)
def _():
    import os
    import subprocess
    import sys

    def quiet_install(command: list):
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

    pip_install_pref = ["pip", "install", "-q"]
    git_pref = "git+https://github.com/"

    packages = [
        [sys.executable, "-m", "pip", "uninstall", "-y", "bluemira"],
        [
            sys.executable,
            "-m",
            *pip_install_pref,
            "--no-cache-dir",
            "--force-reinstall",
            git_pref + "josieapeters/bluemira-bbt.git@develop",
        ],
        ["apt-get", "update", "-q"],
        ["apt-get", "install", "-y", "-q", "libglu1-mesa", "libgl1"],
        pip_install_pref
        + [
            git_pref + "Fusion-Power-Plant-Framework/bluemira-spherical-tokamak",
        ],
        pip_install_pref + [git_pref + "ukaea/PROCESS@v3.4.1"],
        pip_install_pref + ["marimo_cad"],
        pip_install_pref + ["cadquery"],
        pip_install_pref + ["pint==0.25.3"],
    ]

    for package in packages:
        quiet_install(package)

    os.environ.setdefault(key="BLUEMIRA_GEOMETRY_BACKEND", value="cadquery")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Establish materials cache
    """)


@app.cell(hide_code=True)
def _(local_designmat_path):
    from bluemira.materials.cache import MaterialCache

    cache = MaterialCache.get_instance()
    cache.load_from_package([
        "bluemira_st.materials",
        "matproplib",
        local_designmat_path.resolve().as_posix(),
    ])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #Scenario
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The client
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <img style="float: right; margin: 10px" width="300" src="https://static0.srcdn.com/wordpress/wp-content/uploads/2025/02/christopher-lloyd-s-doc-brown-stares-at-the-camera-in-back-to-the-future.jpg?q=70&fit=crop&w=1568&h=1078&dpr=1" title="Universal Pictures">

    We've been approached by a client who needs us to help him **design a fusion reactor to power his time machine**. He seems a little chaotic but his enthusiasm is infectious and we agree to help him in a quest of scientific and engineering exploration.

    He has previously used nuclear fission, so we know his time travelling device works. However, he can't get his hands on any more Plutonium and would prefer a more powerful and safer device.

    He has a couple of requirements,

    1. 1.8 GW of fusion power
    2. As small a device as we can manage

    From our new fusion expertise, we know that a Spherical Tokamak will be our best bet at achieving a smaller machine.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Reactor 1
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Import modules we'll need
    """)


@app.cell
def _():
    from dataclasses import dataclass

    import marimo_cad as cad
    import numpy as np
    from bluemira.base.builder import Builder
    from bluemira.base.components import Component, ComponentT, PhysicalComponent
    from bluemira.base.designer import Designer
    from bluemira.base.parameter_frame import Parameter, ParameterFrame
    from bluemira.base.reactor import ComponentManager, Reactor
    from bluemira.base.reactor_config import ReactorConfig
    from bluemira.builders.plasma import Plasma
    from bluemira.builders.tools import apply_component_display_options
    from bluemira.display import plot_2d
    from bluemira.display.palettes import BLUE_PALETTE
    from bluemira.display.plotter import PlotOptions
    from bluemira.equilibria.coils._grouping import CoilSet
    from bluemira.geometry.face import BluemiraFace
    from bluemira.geometry.optimisation import GeomOptimisationProblem
    from bluemira.geometry.optimisation._optimise import (
        GeomOptimiserResult,
    )
    from bluemira.geometry.optimisation.typed import GeomConstraintT
    from bluemira.geometry.parameterisations import (
        GeometryParameterisation,
        PictureFrame,
    )
    from bluemira.geometry.tools import (
        distance_to,
        extrude_shape,
        interpolate_bspline,
        make_polygon,
        offset_wire,
        sweep_shape,
    )
    from bluemira.geometry.wire import BluemiraWire
    from matplotlib import pyplot as plt

    from bluemira_st.blanket.manager import BreedingBlanket
    from bluemira_st.build_routines import (
        build_bb,
        build_is,
        build_pf_coils,
        build_plasma,
        build_reference_equilibrium,
        build_tf_coils,
    )
    from bluemira_st.inboard_shield.manager import IS
    from bluemira_st.params import BluemiraSTParams
    from bluemira_st.pf_coil.manager import PFCoil
    from bluemira_st.radial_build.run_process import radial_build
    from bluemira_st.tf_coil.manager import TFCoil

    return (
        BLUE_PALETTE,
        BluemiraFace,
        BluemiraSTParams,
        BluemiraWire,
        BreedingBlanket,
        Builder,
        CoilSet,
        Component,
        ComponentManager,
        ComponentT,
        Designer,
        GeomConstraintT,
        GeomOptimisationProblem,
        GeomOptimiserResult,
        GeometryParameterisation,
        IS,
        PFCoil,
        Parameter,
        ParameterFrame,
        PhysicalComponent,
        PictureFrame,
        Plasma,
        PlotOptions,
        Reactor,
        ReactorConfig,
        TFCoil,
        apply_component_display_options,
        build_bb,
        build_is,
        build_pf_coils,
        build_plasma,
        build_reference_equilibrium,
        build_tf_coils,
        cad,
        dataclass,
        distance_to,
        extrude_shape,
        interpolate_bspline,
        make_polygon,
        np,
        offset_wire,
        plot_2d,
        plt,
        radial_build,
        sweep_shape,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ###Parameters and Configuration
    """)


@app.cell
def _(mo):
    major_radius = mo.ui.text(value="4.5", label="${R_0}$ (Major radius)")
    aspect_ratio = mo.ui.text(value="1.8", label="$A$ (Aspect ratio)")
    n_TFs = mo.ui.text(value="12", label="Number of Toroidal Field Coils")

    mo.vstack([major_radius, aspect_ratio, n_TFs])
    return aspect_ratio, major_radius, n_TFs


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Run the next two cells to set your parameter choices and set the configuration file for building your spherical tokamak.
    """)


@app.cell(hide_code=True)
def _(aspect_ratio, major_radius, n_TFs):
    params = {
        "n_PF": {
            "value": 10,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Number of PF coils",
        },
        "n_TF": {
            "value": int(n_TFs.value),
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Number of TF coils",
        },
        "R_0": {
            "value": float(major_radius.value),
            "unit": "meter",
            "source": "Input",
            "long_name": "Major radius",
        },
        "z_0": {
            "value": 0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "z-coordinate of the plasma centre radius",
        },
        "A": {
            "value": float(aspect_ratio.value),
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Plasma aspect ratio",
        },
        "I_p": {
            "value": 0,
            "unit": "megaampere",
            "source": "PROCESS",
            "long_name": "Plasma current",
        },
        "B_0": {
            "value": 3.0,
            "unit": "tesla",
            "source": "Input",
            "long_name": "Toroidal field at R_0",
        },
        "l_i": {
            "value": 0.3,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Normalised internal plasma inductance",
        },
        "beta_p": {
            "value": 0,
            "unit": "dimensionless",
            "source": "PROCESS",
            "long_name": "Ratio of plasma pressure to poloidal magnetic pressure",
        },
        "delta": {
            "value": 0.5,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Last closed surface plasma triangularity",
        },
        "delta_95": {
            "value": 0,
            "unit": "dimensionless",
            "source": "PROCESS",
            "long_name": "95th percentile plasma triangularity",
        },
        "kappa": {
            "value": 2.8,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Last closed surface plasma elongation",
        },
        "kappa_95": {
            "value": 0,
            "unit": "dimensionless",
            "source": "PROCESS",
            "long_name": "95th percentile plasma elongation",
        },
        "q_95": {
            "value": 6.0,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Plasma safety factor at the 95th percentile flux surface",
        },
        "shaf_shift": {
            "value": 1.0,
            "unit": "meter",
            "source": "equilibria",
            "long_name": "Shafranov shift of plasma (geometric=>magnetic)",
        },
        "tf_cl_ib_x": {
            "value": 0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "TF coil center line inboard x-coordinate",
        },
        "tf_cl_ob_x": {
            "value": 0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "TF coil center line outboard x-coordinate",
        },
        "tf_wp_depth": {
            "value": 0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "Total TF coil thickness in y-direction",
        },
        "tf_wp_width": {
            "value": 0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "Total TF coil thickness in z-direction",
        },
        "TF_ripple_limit": {
            "value": 0.6,
            "unit": "percent",
            "source": "Input",
            "long_name": "TF coil ripple limit",
        },
        "g_cs_tf": {
            "value": 0.0,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between CS and TF",
        },
        "g_ts_tf": {
            "value": 0.01,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between TS and TF",
        },
        "g_vv_bb": {
            "value": 0.01,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between VV and BB",
        },
        "g_vv_ts": {
            "value": 0.01,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between VV and TS",
        },
        "r_cs_in": {
            "value": 0.3,
            "unit": "meter",
            "source": "Input",
            "long_name": "Central Solenoid inner radius",
        },
        "tk_bb_ob": {
            "value": 1.0,
            "unit": "meter",
            "source": "Input",
            "long_name": "Outboard blanket thickness",
        },
        "tk_cs": {
            "value": 0.25,
            "unit": "meter",
            "source": "Input",
            "long_name": "Central Solenoid radial thickness",
        },
        "tk_sol_ib": {
            "value": 0.1,
            "unit": "meter",
            "source": "Input",
            "long_name": "Inboard SOL thickness",
        },
        "tk_sol_ob": {
            "value": 0.1,
            "unit": "meter",
            "source": "Input",
            "long_name": "Outboard SOL thickness",
        },
        "tk_tf_front_ib": {
            "value": 0.0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "TF coil inboard steel front plasma-facing",
        },
        "tk_tf_nose": {
            "value": 0.4,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "TF coil inboard nose thickness",
        },
        "tk_tf_side": {
            "value": 0.05,
            "unit": "meter",
            "source": "Input",
            "long_name": "TF coil inboard case minimum side wall thickness",
        },
        "tk_ts": {
            "value": 0.05,
            "unit": "meter",
            "source": "Input",
            "long_name": "TS thickness",
        },
        "r_tf_in_centre": {
            "value": 0.0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "Inboard radius of the TF coil WP centre",
        },
        "r_tf_corner_inner": {
            "value": 1.0,
            "unit": "meter",
            "source": "Input",
            "long_name": "Radius of the TF coil inner corner (poloidal plane)",
        },
        "r_tf_corner_outer": {
            "value": 1.0,
            "unit": "meter",
            "source": "Input",
            "long_name": "Radius of the TF coil outer corner (poloidal plane)",
        },
        "g_pf_tf": {
            "value": 0.2,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between PF and TF coils",
        },
        "fw_psi_n": {
            "value": 1.05,
            "unit": "dimensionless",
            "source": "Input",
            "long_name": "Normalised psi boundary to fit FW to",
        },
        "tk_pf_insulation": {
            "value": 0.01,
            "unit": "meter",
            "source": "Input",
            "long_name": "PF coil insulation thickness",
        },
        "tk_pf_casing": {
            "value": 0.05,
            "unit": "meter",
            "source": "Input",
            "long_name": "PF coil casing thickness",
        },
        "tk_cs_insulation": {
            "value": 0.005,
            "unit": "meter",
            "source": "Input",
            "long_name": "Thickness of the CS coil insulation",
        },
        "tk_cs_casing": {
            "value": 0.001,
            "unit": "meter",
            "source": "Input",
            "long_name": "Thickness of the CS coil casing",
        },
        "r_pf_corner": {
            "value": 0,
            "unit": "meter",
            "source": "Input",
            "long_name": "PF coil corner radius",
        },
        "r_cs_corner": {
            "value": 0,
            "unit": "meter",
            "source": "Input",
            "long_name": "CS coil corner radius",
        },
        "g_tf_cs_internal": {
            "value": 0.01,
            "unit": "meter",
            "source": "Input",
            "long_name": "Gap between TF coils and internal CS coils",
        },
        "tk_tf_inboard": {
            "value": 0.0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "TF coil inboard",
        },
        "tk_vv_in": {
            "value": 0.0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "VV inboard thickness",
        },
        "tk_sh_in": {
            "value": 0.0,
            "unit": "meter",
            "source": "PROCESS",
            "long_name": "Inboard shield thickness",
        },
    }
    return (params,)


@app.cell(hide_code=True)
def _(local_indat_path, params):
    build_config = {
        "params": params,
        "radial_build": {
            "run_mode": "run",
            "input_in_dat_path": local_indat_path,
            "read_dir": ".",
            "run_dir": ".",
            "plot": False,
        },
        "reference_fbe": {
            "plot_setup": False,
            "plot": False,
            "coilset": {"coil_discretisation": 0.1},
            "grid": {"nx": 100, "nz": 200},
            "solver": {"plot": False, "iter_err_max": 1e-2},
            "optimisation": {"gamma": 1e-8, "constraint": {"n_points": 5}},
        },
        "plasma": {},
        "tf_coils": {
            "run_mode": "run",
            "file_path": "./TFCoilDesign.json",
            "plot": False,
            "material": {
                "Winding Pack": "Toroidal_Field_Coil_2015",
                "Casing": "Toroidal_Field_Coil_2015",
                "Insulation": "Toroidal_Field_Coil_2015",
            },
            "problem_class": "bluemira.builders.tf_coils::RippleConstrainedLengthGOP",
            "problem_settings": {
                "ripple_selector": {
                    "cls": "bluemira.builders.tf_coils::EquispacedSelector",
                    "args": {"n_rip_points": 20, "x_frac": 0.5},
                },
                "nx": 3,
                "ny": 3,
            },
            "optimisation_settings": {
                "algorithm_name": "SLSQP",
                "conditions": {"max_eval": 200, "ftol_rel": 1e-6},
            },
        },
        "pf_coils": {
            "verbose": False,
            "material": {
                "Ground Insulation": "Poloidal_Field_Coil",
                "Winding Pack": "Poloidal_Field_Coil",
                "Casing": "Poloidal_Field_Coil",
            },
        },
    }
    return (build_config,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Build the reactor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    First we specify a Reactor object
    """)


@app.cell
def _(BreedingBlanket, IS, PFCoil, Plasma, Reactor, TFCoil):
    class SimpleSTReactor(Reactor):
        """Our first spherical tokamak reactor."""

        plasma: Plasma
        tf_coil: TFCoil
        blanket: BreedingBlanket
        inboard_shield: IS
        pf_coil: PFCoil

    return (SimpleSTReactor,)


@app.cell
def _(
    build_bb,
    build_is,
    build_pf_coils,
    build_plasma,
    build_reference_equilibrium,
    build_tf_coils,
    interpolate_bspline,
    radial_build,
):
    def build_reactor(reactor_config, ReactorClass, tf_coil_builder=build_tf_coils):
        reactor = ReactorClass(
            "Bluemira Spherical Tokamak Example",
            n_sectors=reactor_config.global_params.n_TF.value,
        )

        radial_build(
            reactor_config.params_for("radial_build").global_params,
            reactor_config.config_for("radial_build"),
        )

        ref_fbe = build_reference_equilibrium(
            reactor_config.params_for("reference_fbe").global_params,
            reactor_config.config_for("reference_fbe"),
        )

        reactor.plasma = build_plasma(
            reactor_config.params_for("plasma"),
            reactor_config.config_for("plasma"),
            ref_fbe,
        )

        reactor.pf_coil = build_pf_coils(
            reactor_config.params_for("pf_coils"),
            reactor_config.config_for("pf_coils"),
            ref_fbe.coilset,
        )

        reactor.tf_coil = tf_coil_builder(
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

        reactor.inboard_shield = build_is(
            reactor_config.params_for("inboard_shield"),
            reactor_config.config_for("inboard_shield"),
            mat_name="EUROFER_MAT",
            ref_fbe=ref_fbe,
        )
        return reactor

    return (build_reactor,)


@app.cell
def _(
    BluemiraSTParams,
    ReactorConfig,
    SimpleSTReactor,
    build_config,
    build_reactor,
):
    reactor_config = ReactorConfig(build_config, BluemiraSTParams)
    reactor = build_reactor(reactor_config, SimpleSTReactor)
    return (reactor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Visualising
    """)


@app.cell
def _(cad, mo, n_TFs):
    def visualise_reactor(reactor):
        reactor_shapes = reactor._build_component_tree(
            "xyz",
            reactor._init_construction_param_values(
                kwargs=dict(n_sectors=int(n_TFs.value)), c_params=None
            ),
        ).get_component_properties("shape", first=False)[0]

        reactor_shapes = [
            {
                "shape": i._shape,
                "color": "pink" if i.label == "LCFS" else "blue",
                "name": i.label,
            }
            for i in reactor_shapes
        ]

        viewer = cad.Viewer()
        viewer.render(reactor_shapes)
        return mo.vstack([viewer])

    return (visualise_reactor,)


@app.cell
def _(reactor, visualise_reactor):
    visualise_reactor(reactor)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reactor 2
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <img style="float: left; margin: 20px" width="400" src="https://images.squarespace-cdn.com/content/v1/51b3dc8ee4b051b96ceb10de/79d5a0c3-d9d1-4759-85d7-73cb009c7f63/Screen+Shot+2023-04-17+at+1.00.35+PM.jpg?format=2500w">

    The reactor is looking great, but in his haste, the client forgot to tell us another important requirement.
    He needs a port in the tokamak to connect it the various wires and cables in his car that acts as the vessel for time travel.

    Ideally, this port will be lower down so minimal amounts of cable are required to link everything up.
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We'll need a new configuration dictionary to build this new device with a port.
    """)


@app.cell
def _(mo):
    port_height = mo.ui.text(value="-4", label="Port height (m)")

    mo.vstack([port_height])
    return (port_height,)


@app.cell(hide_code=True)
def _(local_indat_path, params, port_height):
    build_config_with_port = {
        "params": params,
        "radial_build": {
            "run_mode": "run",
            "input_in_dat_path": local_indat_path,
            "read_dir": ".",
            "run_dir": ".",
            "plot": False,
        },
        "reference_fbe": {
            "plot_setup": False,
            "plot": False,
            "coilset": {"coil_discretisation": 0.1},
            "grid": {"nx": 100, "nz": 200},
            "solver": {"plot": False, "iter_err_max": 1e-2},
            "optimisation": {"gamma": 1e-8, "constraint": {"n_points": 5}},
        },
        "plasma": {},
        "tf_coils": {
            "material": {
                "Winding Pack": "Toroidal_Field_Coil_2015",
                "Casing": "Toroidal_Field_Coil_2015",
                "Insulation": "Toroidal_Field_Coil_2015",
            },
            "optimisation_settings": {
                "algorithm_name": "SLSQP",
                "conditions": {"max_eval": 200, "ftol_rel": 1e-6},
            },
            "params": {
                "min_port_surface_area": {
                    "value": 12,
                    "unit": "m^2",
                    "source": "Input",
                    "long_name": "Minimum surface area of the upper port",
                },
                "min_plasma_dist": {
                    "value": 1,
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Minimum distance between the tf and the plasma",
                },
                "g_tf_up": {
                    "value": 0.8,
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Gap between the TF coil (wp) and the upper port",
                },
                "up_ob_inset": {
                    "value": 2,
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Upper port outboard inset, inset from tf_r_max",
                },
                "up_ib_inset": {
                    "value": 4,
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Upper port inboard inset, inset from tf_r_start",
                },
            },
        },
        "pf_coils": {
            "verbose": False,
            "material": {
                "Ground Insulation": "Poloidal_Field_Coil",
                "Winding Pack": "Poloidal_Field_Coil",
                "Casing": "Poloidal_Field_Coil",
            },
        },
        "lower_port": {
            "params": {
                "tk_wall": {
                    "value": 0.1,
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Major radius",
                },
                "z_height": {
                    "value": int(port_height.value),
                    "unit": "m",
                    "source": "Input",
                    "long_name": "Reference vertical coordinate",
                },
            }
        },
    }
    return (build_config_with_port,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Adding a port
    """)


@app.cell
def _(
    BluemiraFace,
    BluemiraWire,
    Builder,
    Component,
    ComponentManager,
    Parameter,
    ParameterFrame,
    PhysicalComponent,
    ReactorConfig,
    dataclass,
    extrude_shape,
    offset_wire,
):
    @dataclass
    class LowerPortBuilderParams(ParameterFrame):
        """Parameters for the Lower port builder"""

        n_TF: Parameter[int]

        tk_wall: Parameter[float]
        z_height: Parameter[float]

    class LowerPortBuilder(Builder):
        """Builder for the lower port of the reactor"""

        params: LowerPortBuilderParams
        param_cls: type[LowerPortBuilderParams] = LowerPortBuilderParams

        LOWER_PORT: str = "LowerPort"

        def __init__(self, params, lower_port_wire: BluemiraWire):
            super().__init__(params, {})
            self.lower_port_wire = lower_port_wire

        def build(self) -> Component:
            """Build component"""
            return self.component_tree(
                xz=None,
                xy=None,
                xyz=[self.build_xyz()],
            )

        def build_xyz(self) -> PhysicalComponent:
            """Build Component xyz"""
            port_inner = offset_wire(self.lower_port_wire, -self.params.tk_wall.value)
            port_xy = BluemiraFace([self.lower_port_wire, port_inner])
            xyz_port = extrude_shape(port_xy, (0, 0, -self.params.z_height.value))
            tf_alpha = 360 / self.params.n_TF.value
            xyz_port.rotate((0, 0, 0), (0, 0, 1), tf_alpha / 2)
            return PhysicalComponent(self.LOWER_PORT, xyz_port)

    class LowerPort(ComponentManager):
        """Lower port of the reactor"""

    def build_lower_port(
        reactor_config: ReactorConfig, up_silhouette: BluemiraWire
    ) -> LowerPort:
        """Build an upper port from a set of parameters."""
        lower_port_builder = LowerPortBuilder(
            reactor_config.params_for("lower_port"), up_silhouette
        )
        return LowerPort(lower_port_builder.build())

    return LowerPort, build_lower_port


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Adjusting the TF coils
    """)


@app.cell
def _(
    BLUE_PALETTE,
    BluemiraFace,
    BluemiraWire,
    Builder,
    CoilSet,
    Component,
    ComponentManager,
    ComponentT,
    Designer,
    GeomConstraintT,
    GeomOptimisationProblem,
    GeomOptimiserResult,
    GeometryParameterisation,
    Parameter,
    ParameterFrame,
    PhysicalComponent,
    PictureFrame,
    PlotOptions,
    apply_component_display_options,
    dataclass,
    distance_to,
    make_polygon,
    np,
    offset_wire,
    plot_2d,
    plt,
    sweep_shape,
):
    TF_w_port_path = "github://examples/tf_coil_with_port.py"
    TF_w_port = bm_st.download(TF_w_port_path, "")
    from tf_coil_with_port import TFCoil_with_port, TFCoilBuilder, TFCoilDesigner

    return TFCoilBuilder, TFCoilDesigner, TFCoil_with_port


@app.cell
def _(BluemiraWire, CoilSet, TFCoilBuilder, TFCoilDesigner, TFCoil_with_port):
    def build_tf_coils_for_port(
        params: dict, build_config: dict, coilset: CoilSet, plasma_lcfs: BluemiraWire
    ) -> TFCoil_with_port:
        """Build a TF coil from a set of parameters."""
        tf_coil_designer = TFCoilDesigner(
            params,
            build_config,
            lcfs=plasma_lcfs,
            coilset=coilset,
        )
        tf_coil_parameterisation, up_face = tf_coil_designer.execute()

        tf_coil_builder = TFCoilBuilder(
            params,
            tf_coil_parameterisation.create_shape(),
        )
        return TFCoil_with_port(tf_coil_builder.build(), up_face)

    return (build_tf_coils_for_port,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Building the second reactor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Our reactor needs re-specifying that a port will be one of its components
    """)


@app.cell
def _(BreedingBlanket, IS, LowerPort, PFCoil, Plasma, Reactor, TFCoil):
    class STReactorWithPort(Reactor):
        """A spherical tokamak with a port."""

        plasma: Plasma
        tf_coil: TFCoil
        blanket: BreedingBlanket
        inboard_shield: IS
        pf_coil: PFCoil
        lower_port: LowerPort

    return (STReactorWithPort,)


@app.cell
def _(
    BluemiraSTParams,
    ReactorConfig,
    STReactorWithPort,
    build_config_with_port,
    build_reactor,
    build_tf_coils_for_port,
):
    reactor_config_with_port = ReactorConfig(build_config_with_port, BluemiraSTParams)
    reactor_with_port = build_reactor(
        reactor_config_with_port, STReactorWithPort, build_tf_coils_for_port
    )
    return reactor_config_with_port, reactor_with_port


@app.cell
def _(build_lower_port, reactor_config_with_port, reactor_with_port):
    reactor_with_port.lower_port = build_lower_port(
        reactor_config_with_port,
        reactor_with_port.tf_coil.upper_port_face,
        #  ref_fbe=ref_fbe,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We'll need a new configuration dictionary to build this new device with a port.
    """)


@app.cell
def _(reactor_with_port, visualise_reactor):
    visualise_reactor(reactor_with_port)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Back to the drawing board!
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Find out more!
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ####If you'd like to learn more about `bluemira`:
    #### - head to our [GitHub repo](https://github.com/Fusion-Power-Plant-Framework/bluemira)
    #### - read our [Nuclear Fusion paper](https://iopscience.iop.org/article/10.1088/1741-4326/aea584).

    ### Collaborate with us!
    ####[bluemira-template-project](https://github.com/Fusion-Power-Plant-Framework/bluemira-template-project): A template for a new Bluemira reactor project
    ####This notebook uses our [Spherical Tokamak example](https://github.com/Fusion-Power-Plant-Framework/bluemira-spherical-tokamak).
    """)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
