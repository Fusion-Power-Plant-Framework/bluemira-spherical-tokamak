import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Initial set-up
    Run the next cell to install bluemira on the server for this notebook.
    """)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from fsspec.implementations.github import GithubFileSystem

    bbt_repo = GithubFileSystem(org="josieapeters", repo="bluemira-bbt")
    bm_st = GithubFileSystem(
        org="Fusion-Power-Plant-Framework",
        repo="bluemira-spherical-tokamak",
        branch="main",
    )

    INDAT_path = "github://studies/first/data/PROCESS/st_regression.IN.DAT"
    MFILE_path = "github://examples/spherical_tokamak/MFILE.DAT"
    TF_path = "github://studies/first/data/TF/TFCoilDesign.json"
    run_dir = "github://studies/first/data/PROCESS/run_dir"
    INDAT = bm_st.download(INDAT_path, "")
    MFILE = bbt_repo.download(MFILE_path, "")
    TF_json = bm_st.download(
        TF_path,
        "",
    )
    local_indat_path = Path("st_regression.IN.DAT")

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

    from bluemira.materials.cache import MaterialCache

    cache = MaterialCache.get_instance()
    cache.load_from_package([
        "bluemira_st.materials",
        "matproplib",
        Path("./design_materials.py").resolve().as_posix(),
    ])

    return (mo, bbt_repo, bm_st, INDAT, MFILE)


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


if __name__ == "__main__":
    app.run()
