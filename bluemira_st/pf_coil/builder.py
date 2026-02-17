

from copy import deepcopy
from dataclasses import dataclass

from bluemira.base.builder import Builder
from bluemira.base.components import Component, PhysicalComponent
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.base.constants import CoilType
from bluemira.builders.pf_coil import PFCoilBuilder, PFCoilPictureFrame
from bluemira.equilibria.coils import CoilSet
from bluemira_st.pf_coil.coilset import  pf_default_params
from bluemira_st.pf_coil.manager import PFCoil

class PFCoilBuilderSTParams(ParameterFrame):
    " parameters for building a PF coil"
    tk_insulation: Parameter[float]
    tk_casing:  Parameter[float]
    r_corner: Parameter[float]
    
def build_pf_coilset(params: dict | ParameterFrame, 
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
            {"r_corner": {"value": pf_default_params.r_corner.value,
                          "unit": pf_default_params.r_corner.unit}},
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