"""Configuration for the Bluemira ST example radiation calculation."""

import numpy as np

RADIATION_CONFIG = {
    "f_imp_core": {
        "H": 1e-1,
        "He": 1e-2,
        "Xe": 1e-4,
        "W": 1e-5,
    },
    "f_imp_sol": {
        "H": 0.0,
        "He": 0.0,
        "Ar": 0.003,
        "Xe": 0.0,
        "W": 0.0,
    },
    "tau_core": np.inf,
    "tau_sol": 10.0,
}
