from bluemira.base.parameter_frame import ParameterFrame
from bluemira.builders.plasma import Plasma, PlasmaBuilder
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.equilibria.profiles import Profile
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.tools import distance_to, interpolate_bspline, offset_wire

from bluemira_st.equlibria.designer import ReferenceFreeBoundaryEquilibriumDesigner


def build_reference_equilibrium(
    params: dict | ParameterFrame,
    build_config: dict,
    # equilibrium_manager: EquilibriumManager,
    lcfs_coords: Coordinates | None,
    profiles: Profile | None,
) -> Equilibrium:
    """
    Build the reference equilibrium for the tokamak and store in
    the equilibrium manager

    Returns
    -------
    :
        The reference equilibrium
    """
    designer = ReferenceFreeBoundaryEquilibriumDesigner(
        params,
        build_config,
        lcfs_coords,
        profiles,
    )
    return designer.execute()


def build_plasma(params, build_config: dict, eq: Equilibrium) -> Plasma:
    """Build EUDEMO plasma from an equilibrium.

    Returns
    -------
    :
        Plasma component manager
    """
    lcfs_loop = eq.get_LCFS()
    lcfs_wire = interpolate_bspline({"x": lcfs_loop.x, "z": lcfs_loop.z}, closed=True)
    builder = PlasmaBuilder(params, build_config, lcfs_wire)
    return Plasma(builder.build())
