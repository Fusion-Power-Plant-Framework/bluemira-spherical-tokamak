from bluemira.base.parameter_frame import ParameterFrame
from bluemira.builders.plasma import Plasma, PlasmaBuilder
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.equilibria.profiles import Profile
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.parameterisations import GeometryParameterisation, PrincetonD
from bluemira.geometry.tools import distance_to, interpolate_bspline, offset_wire
from bluemira.geometry.wire import BluemiraWire

from bluemira_st.equlibria.designer import ReferenceFreeBoundaryEquilibriumDesigner
from bluemira_st.tf_coil.builder import TFCoilBuilder
from bluemira_st.tf_coil.designer import TFCoilDesigner, TFInitialShapeDesigner
from bluemira_st.tf_coil.manager import TFCoil

from bluemira.builders.pf_coil import PFCoilBuilder
from bluemira.base.components import Component
from bluemira.base.constants import CoilType
from bluemira.builders.pf_coil import PFCoilPictureFrame
from bluemira.equilibria.coils import CoilSet
from bluemira_st.pf_coil.manager import PFCoil
from bluemira_st.pf_coil.coilset import  pf_default_params
from bluemira_st.vacuum_vessel import VacuumVessel, VacuumVesselBuilder

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


def build_plasma(
    params: dict | ParameterFrame,
    build_config: dict,
    lcfs_wire,
    # eq: Equilibrium
) -> Plasma:
    """Build EUDEMO plasma from an equilibrium.

    Returns
    -------
    :
        Plasma component manager
    """
    # lcfs_loop = eq.get_LCFS()
    # lcfs_wire = interpolate_bspline({"x": lcfs_loop.x, "z": lcfs_loop.z}, closed=True)
    builder = PlasmaBuilder(params, build_config, lcfs_wire)
    return Plasma(builder.build())


def build_initial_tf_centerline(
    params: dict | ParameterFrame, build_config: dict, lcfs_wire: BluemiraWire
) -> PrincetonD:
    """Build the initial TF coil shapes from an equilibrium.

    Returns
    -------
    :
        The inboard and outboard TF coil shapes
    """
    return TFInitialShapeDesigner(params, build_config, lcfs_wire).run()


def build_tf_coils(
    params: dict | ParameterFrame,
    build_config: dict,
    tf_initial_cl: PrincetonD,
    plasma_lcfs: BluemiraWire,
) -> TFCoil:
    """Build the TF coils from the initial TF coil shapes.

    Returns
    -------
    :
        The TF coil shapes
    """
    tf_cl, tf_wp_xs = TFCoilDesigner(
        params, build_config, tf_initial_cl, plasma_lcfs
    ).execute()
    builder = TFCoilBuilder(params, build_config, tf_cl.create_shape(), tf_wp_xs)
    return TFCoil(builder.build())


def build_pf_coils(params: dict | ParameterFrame, 
                   build_config: dict, 
                   coilset: CoilSet):
    """Build all PF coils from a CoilSet using the built-in Bluemira PFCoilBuilder.

    Returns
    -------
    :
        The PF coil shapes
    """ 
    pf_children = []

    for name in coilset.name:
        coil = coilset[name]

        # Create wire using PictureFrame parameterisation
        wire = PFCoilPictureFrame(
            {"r_corner": {"value": 0.12, "unit": "m"}},
            coil
        ).execute()

        # Per-coil parameters
        per_params = {
            "ctype": {"value": coil.ctype.name, "unit": ""},
            "n_TF": {
                "value": pf_default_params.n_TF.value,
                "unit": pf_default_params.n_TF.unit,
            },
            "tk_insulation": {
                "value": pf_default_params.tk_insulation.value,
                "unit": pf_default_params.tk_insulation.unit,
            },
            "tk_casing": {
                "value": pf_default_params.tk_casing.value,
                "unit": pf_default_params.tk_casing.unit,
            },
            }


        # Build config with unique name
        per_build_config = {"name": name}

        # Use built-in PFCoil Builder to create individual coils
        pf_component = PFCoilBuilder(per_params, per_build_config, wire).build()
        pf_children.append(pf_component)
    pf_group = Component("PF coils", children=pf_children)
    return PFCoil(pf_group)

def build_vacuum_vessel(params, build_config, ivc_koz) -> VacuumVessel:
    """Build the vacuum vessel around the given IVC keep-out zone.

    Returns
    -------
    :
        Vacuum vessel component manager
    """
    vv_builder = VacuumVesselBuilder(params, build_config, ivc_koz)
    return VacuumVessel(vv_builder.build())