from bluemira.base.parameter_frame import ParameterFrame
from bluemira.builders.plasma import Plasma, PlasmaBuilder
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.equilibria.profiles import Profile
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.parameterisations import GeometryParameterisation, PrincetonD
from bluemira.geometry.tools import distance_to, interpolate_bspline, offset_wire
from bluemira.geometry.wire import BluemiraWire

from bluemira_st.equlibria.designer import ReferenceFreeBoundaryEquilibriumDesigner
from bluemira_st.tf_coil.designer import TFInitialShapeDesigner


def build_reference_equilibrium(
    params: dict | ParameterFrame,
    build_config: dict,
    # equilibrium_manager: EquilibriumManager,
    lcfs_wire: BluemiraWire | None,
    profiles: Profile | None,
    tf_cl: GeometryParameterisation | None,
) -> Equilibrium:
    """
    Build the reference equilibrium for the tokamak and store in
    the equilibrium manager.

    Returns
    -------
    :
        The reference equilibrium
    """
    designer = ReferenceFreeBoundaryEquilibriumDesigner(
        params,
        build_config,
        lcfs_wire,
        profiles,
        tf_cl_wire=tf_cl.create_shape() if tf_cl else None,
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


def build_initial_tf_shapes(
    params, build_config: dict, lcfs_wire: BluemiraWire
) -> tuple[PrincetonD, BluemiraWire]:
    """Build the initial TF coil shapes from an equilibrium.

    Returns
    -------
    :
        The inboard and outboard TF coil shapes
    """
    tf_initial_cl, tf_face = TFInitialShapeDesigner(
        params, build_config, lcfs_wire
    ).run()
    return tf_initial_cl, tf_face
