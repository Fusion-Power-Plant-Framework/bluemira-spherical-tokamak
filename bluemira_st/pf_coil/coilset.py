from dataclasses import dataclass
from bluemira.base.parameter_frame import Parameter, ParameterFrame
from bluemira.equilibria.coils import Coil, CoilSet
from bluemira.base.constants import CoilType

# ----------------------------
# PF COIL PARAMETER FRAME
# ----------------------------

@dataclass
class PFParams(ParameterFrame):
    n_TF: Parameter[int]
    tk_insulation: Parameter[float]
    tk_casing: Parameter[float]

# Default PF parameters
pf_default_params = PFParams.from_dict({
    "n_TF":          {"value": 12, "unit": ""},
    "tk_insulation": {"value": 0.02, "unit": "m"},
    "tk_casing":     {"value": 0.04, "unit": "m"},
})

# ----------------------------
# PF COILSET (GEOMETRY)
# ----------------------------

pf_coilset = CoilSet(
    Coil(x=7.5, z=0.0,  dx=0.40, dz=0.70, name="PF1", ctype=CoilType.PF),
    Coil(x=6.8, z=3.0,  dx=0.35, dz=0.60, name="PF2", ctype=CoilType.PF),
    Coil(x=6.8, z=-3.0, dx=0.35, dz=0.60, name="PF3", ctype=CoilType.PF),
)

pf_coilset_step_like = CoilSet(

    Coil(x=4.25, z= 9.55, dx=0.40, dz=0.70, name="PF1",  ctype=CoilType.PF),
    Coil(x=1.50, z= 9.44, dx=0.40, dz=0.70, name="PF2",  ctype=CoilType.PF),
    Coil(x=8.00, z= 9.44, dx=0.40, dz=0.70, name="PF3",  ctype=CoilType.PF),

    Coil(x=1.69, z= 7.89, dx=0.40, dz=0.70, name="PF4",  ctype=CoilType.PF),
    Coil(x=8.25, z= 6.56, dx=0.40, dz=0.70, name="PF5",  ctype=CoilType.PF),

    Coil(x=10.73, z= 2.11, dx=0.40, dz=0.70, name="PF6",  ctype=CoilType.PF),
    Coil(x=10.73, z=-2.17, dx=0.40, dz=0.70, name="PF7",  ctype=CoilType.PF),

    Coil(x=8.25, z=-6.63, dx=0.40, dz=0.70, name="PF8",  ctype=CoilType.PF),
    Coil(x=1.69, z=-7.93, dx=0.40, dz=0.70, name="PF9",  ctype=CoilType.PF),

    Coil(x=1.50, z=-9.50, dx=0.40, dz=0.70, name="PF10", ctype=CoilType.PF),
    Coil(x=8.00, z=-9.52, dx=0.40, dz=0.70, name="PF11", ctype=CoilType.PF),
    Coil(x=4.25, z=-9.62, dx=0.40, dz=0.70, name="PF12", ctype=CoilType.PF),
    # Thin inboard coils (low x)
    Coil(x=1.60, z=  5.01, dx=0.20, dz=0.70, name="PF13", ctype=CoilType.PF),
    Coil(x=1.62, z= -5.04, dx=0.20, dz=0.70, name="PF14", ctype=CoilType.PF),
)