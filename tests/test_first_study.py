import runpy
from pathlib import Path


def _skip_polyscope():
    try:
        import polyscope  # noqa: F401, PLC0415
    except ImportError:
        return True
    else:
        return False


def test_first_study():
    """
    Test that the simple reactor script works.
    Effectively tests parameters etc. are still accurate.
    """
    first_study_path = (
        Path(Path(__file__).parent.parent, "studies/first/reactor.py")
        .resolve()
        .as_posix()
    )
    runpy.run_path(str(first_study_path), run_name="__main__")
