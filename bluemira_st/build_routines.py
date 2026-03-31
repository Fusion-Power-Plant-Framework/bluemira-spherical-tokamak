from bluemira.base.parameter_frame import ParameterFrame
from bluemira.builders.plasma import Plasma, PlasmaBuilder
from bluemira.equilibria.coils._grouping import CoilSet
from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.geometry.tools import (
    interpolate_bspline,
)
from bluemira.geometry.wire import BluemiraWire

from bluemira_st.blanket.builder import BBBuilder
from bluemira_st.blanket.manager import BB
from bluemira_st.equilibria.designer import ReferenceFreeBoundaryEquilibriumDesigner
from bluemira_st.pf_coil.builder import build_pf_coils_component
from bluemira_st.pf_coil.manager import PFCoil
from bluemira_st.tf_coil.builder import TFCoilBuilder
from bluemira_st.tf_coil.designer import TFCoilDesigner
from bluemira_st.tf_coil.manager import TFCoil

from bluemira_st.inboard_shield.builder import ISBuilder
from bluemira_st.inboard_shield.manager import IS

def build_reference_equilibrium(
    params: dict | ParameterFrame,
    build_config: dict,
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
    )
    return designer.execute()


def build_plasma(
    params: dict | ParameterFrame, build_config: dict, eq: Equilibrium
) -> Plasma:
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


def build_tf_coils(
    params: dict | ParameterFrame,
    build_config: dict,
    coilset: CoilSet,
    plasma_lcfs: BluemiraWire,
) -> TFCoil:
    """Build the TF coils from the initial TF coil shapes.

    Returns
    -------
    :
        The TF coil shapes
    """
    tf_cl, tf_wp_xs = TFCoilDesigner(
        params, build_config, coilset, plasma_lcfs
    ).execute()
    builder = TFCoilBuilder(params, build_config, tf_cl.create_shape(), tf_wp_xs)
    return TFCoil(builder.build())


def build_bb(
    params: dict | ParameterFrame,
    build_config: dict,
    mat_name: str,
    ref_fbe: Equilibrium,
):
    """Build the breeder blanket component."""
    return BB(BBBuilder(params, build_config, mat_name, ref_fbe).build())


def build_pf_coils(
    params: dict | ParameterFrame,
    build_config: dict,
    coilset: CoilSet,
) -> PFCoil:
    """
    Build the PF coils for the reactor,
    based on the coilset from the free boundary equilibrium.

    Returns
    -------
    :
        PF coil component manager
    """
    component = build_pf_coils_component(params, build_config, coilset)
    return PFCoil(component, coilset)

def build_is(
        params: dict | ParameterFrame,
        build_config: dict,
        mat_name: str,
        ref_fbe: Equilibrium
        ):
    """Build the inboard shield component."""
    is_comp = IS(ISBuilder(params, build_config, mat_name, ref_fbe).build())
    return is_comp
