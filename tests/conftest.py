from contextlib import suppress
from unittest import mock

import matplotlib as mpl
import pytest


def pytest_addoption(parser):
    """
    Add a custom command line option to pytest to control plotting and longrun.
    """
    parser.addoption(
        "--plotting-on",
        action="store_true",
        default=False,
        help="switch on interactive plotting in tests",
    )


def pytest_configure(config):
    """
    Configure pytest with the plotting and longrun command line options.
    """
    if not config.option.plotting_on:
        # We're not displaying plots so use a display-less backend
        mpl.use("Agg")
        # Disable CAD viewer by mocking out every show_cad entry point.
        # The ``_geometryapi`` dispatcher star-imports from the active backend
        # (`_freecad.api` or `_cadquery`), which binds ``show_cad`` on
        # ``_geometryapi`` at import time — patching the underlying backend
        # alone does NOT propagate, so we mock all three module-level names.
        with suppress(ImportError):
            mock.patch("bluemira.codes._polyscope.ps").start()
        for _name in (  # noqa: RUF052
            "bluemira.codes.cadapi._freecad.api.show_cad",
            "bluemira.codes.cadapi._cadquery.show_cad",
            "bluemira.codes._geometryapi.show_cad",
        ):
            with suppress(ImportError, AttributeError):
                mock.patch(_name).start()


@pytest.fixture(autouse=True)
def _plot_show_and_close(request):
    """Fixture to show and close plots.

    Notes
    -----
    Does not do anything if testclass marked with 'classplot'
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415

    cls = request.node.getparent(pytest.Class)

    if cls and "classplot" in cls.keywords:
        yield
    else:
        yield
        clstitle = "" if cls is None else cls.name
        for fig in list(map(plt.figure, plt.get_fignums())):
            fig.suptitle(
                f"{fig.get_suptitle()} {clstitle}::"
                f"{request.node.getparent(pytest.Function).name}"
            )
        plt.show()
        plt.close()


@pytest.fixture(scope="class", autouse=True)
def _plot_show_and_close_class(request):
    """Fixture to show and close plots for marked classes.

    Notes
    -----
    Only shows and closes figures on classes marked with 'classplot'
    """
    import matplotlib.pyplot as plt  # noqa: PLC0415

    if "classplot" in request.keywords:
        yield
        clstitle = request.node.getparent(pytest.Class).name

        for fig in list(map(plt.figure, plt.get_fignums())):
            fig.suptitle(f"{fig.get_suptitle()} {clstitle}")
        plt.show()
        plt.close()
    else:
        yield
