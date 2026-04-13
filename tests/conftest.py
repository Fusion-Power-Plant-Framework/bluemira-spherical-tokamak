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
