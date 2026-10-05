import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Bluemira Spherical Tokamak Tutorial
    """)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Introduction
    ###[`Bluemira`](https://github.com/Fusion-Power-Plant-Framework/bluemira) is an integrated inter-disciplinary design tool for future fusion reactors. It incorporates several modules to carry out a range of typical conceptual fusion reactor design activities.

    ####This notebook uses our [Spherical Tokamak example](https://github.com/Fusion-Power-Plant-Framework/bluemira-spherical-tokamak).

    ####If you'd like to learn more about `bluemira`, head to our [GitHub repo](https://github.com/Fusion-Power-Plant-Framework/bluemira) and/or read our [Nuclear Fusion paper](https://iopscience.iop.org/article/10.1088/1741-4326/aea584).
    """)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Tutorial structure
    In this tutorial we will:

    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Initial set-up
    Run the next two cells to install `bluemira` on the server for this notebook and establish cache for the materials we need. This will
    take a couple of minutes.

    The code in the cell is unique for working in marimo notebooks. If you install
    `bluemira` locally, the setup will be simpler. :)
    """)

@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)

@app.cell(hide_code=True)
def _():
    from pathlib import Path
    from fsspec.implementations.github import GithubFileSystem

    bm_st = GithubFileSystem(
        org="Fusion-Power-Plant-Framework",
        repo="bluemira-spherical-tokamak",
        branch="main",
    )

    INDAT_path = "github://studies/first/data/PROCESS/st_regression.IN.DAT"
    INDAT = bm_st.download(INDAT_path, "")
    local_indat_path = Path("st_regression.IN.DAT")

    TF_path = "github://studies/first/data/TF/TFCoilDesign.json"
    TF_json = bm_st.download(TF_path, "", )
    return (INDAT, TF_json)


@app.cell(hide_code=True)
def _():
    import os
    import subprocess
    import sys
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "bluemira"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--force-reinstall",
            "-q",
            "git+https://github.com/josieapeters/bluemira-bbt.git@develop",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    os.environ.setdefault(key="BLUEMIRA_GEOMETRY_BACKEND", value="cadquery")

    subprocess.run(
        ["apt-get", "update", "-q"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        ["apt-get", "install", "-y", "-q", "libglu1-mesa", "libgl1"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        [
            "pip",
            "install",
            "-q",
            "git+https://github.com/Fusion-Power-Plant-Framework/bluemira-spherical-tokamak",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        [
            "pip",
            "install",
            "-q",
            "git+https://github.com/ukaea/PROCESS@v3.4.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        [
            "pip",
            "install",
            "-q",
            "marimo_cad",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    subprocess.run(
        [
            "pip",
            "install",
            "-q",
            "cadquery",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


@app.cell(hide_code=True)
def _():
    from bluemira.materials.cache import MaterialCache

    cache = MaterialCache.get_instance()
    cache.load_from_package([
        "bluemira_st.materials",
        "matproplib",
        Path("./design_materials.py").resolve().as_posix(),
    ])

    return ()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Import from `bluemira` and `bluemira spherical tokamak`.
    The next cell imports some modules we'll need for making our spherical tokamak.
    """)


@app.cell()
def _():
    import marimo_cad as cad
    from bluemira.base.reactor import Reactor
    from bluemira.base.reactor_config import ReactorConfig
    from bluemira.builders.plasma import Plasma
    from bluemira.geometry.tools import interpolate_bspline

    from bluemira_st.blanket.manager import BB
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
        BB,
        BluemiraSTParams,
        IS,
        PFCoil,
        Plasma,
        Reactor,
        ReactorConfig,
        TFCoil,
        build_bb,
        build_is,
        build_pf_coils,
        build_plasma,
        build_reference_equilibrium,
        build_tf_coils,
        cad,
        interpolate_bspline,
        radial_build,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""

    """)


@app.cell()
def _():


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Parameter choices
    In the below cell is the full json dictionary of all our parameter values.

    The cell is "hidden" so that it collapses when you're not viewing it. Click to take a look to see what's in there.
    """)

@app.cell(hide_code=True)
def _():
    major_radius = mo.ui.text(value="4.5", label="${R_0}$ (Major radius)")
    aspect_ratio = mo.ui.text(value="1.8", label="$A$ (Aspect ratio)")
    delta = mo.ui.text(value="0.5", label="${\delta}$ (Triangularity)")
    n_TFs = mo.ui.text(value="12", label="Number of Toroidal Field Coils")
    return (major_radius, aspect_ratio, delta, n_TFs)


@app.cell()
def _():
    mo.vstack([major_radius, aspect_ratio, delta, n_TFs])


@app.cell(hide_code=True)
def _():
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
            "value": float(delta.value),
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
def _(mo):
    mo.md(r"""
        Our parameters are then used as an input for the build_config below.
    """)

@app.cell(hide_code=True)
def _(params):
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
            "file_path": TF_json,
            "plot": True,
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
    ## Build the reactor
    """)


@app.cell
def _(BB, IS, PFCoil, Plasma, Reactor, TFCoil):
    class MyReactor(Reactor):
        """A simple reactor."""

        plasma: Plasma
        tf_coil: TFCoil
        blanket: BB
        inboard_shield: IS
        pf_coil: PFCoil

    return (MyReactor,)


@app.cell()
def _(
    BluemiraSTParams,
    MyReactor,
    ReactorConfig,
    build_bb,
    build_config,
    build_is,
    build_pf_coils,
    build_plasma,
    build_reference_equilibrium,
    build_tf_coils,
    interpolate_bspline,
    radial_build,
):
    reactor_config = ReactorConfig(build_config, BluemiraSTParams)
    reactor = MyReactor(
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

    reactor.inboard_shield = build_is(
        reactor_config.params_for("inboard_shield"),
        reactor_config.config_for("inboard_shield"),
        mat_name="EUROFER_MAT",
        ref_fbe=ref_fbe,
    )
    return (reactor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
        Let's view our reactor with our default input values.
    """)


@app.cell(hide_code=True)
def _(reactor, cad, mo):
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
    mo.vstack([viewer])


if __name__ == "__main__":
    app.run()
